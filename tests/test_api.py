import io
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, engine, SessionLocal
from app.ml.dataset_generator import generate_synthetic_dataset

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=engine)
    yield


def login(email: str, password: str) -> dict:
    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def faculty_headers():
    return login("faculty@edupredict.local", "Faculty@123")


@pytest.fixture(scope="module")
def admin_headers():
    return login("admin@edupredict.local", "Admin@123")


@pytest.fixture(scope="module")
def student_headers():
    return login("student@edupredict.local", "Student@123")


def test_login_rejects_bad_credentials():
    r = client.post("/auth/login", json={"email": "admin@edupredict.local", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_rejects_invalid_email():
    # Email format is not validated at login; unknown accounts get 401
    r = client.post("/auth/login", json={"email": "not-an-email", "password": "Admin@123"})
    assert r.status_code == 401


def test_me_requires_auth():
    r = client.get("/me")
    assert r.status_code == 401


def test_me_returns_user(faculty_headers):
    r = client.get("/me", headers=faculty_headers)
    assert r.status_code == 200
    assert r.json()["role"] == "faculty"


def test_student_cannot_list_students(student_headers):
    r = client.get("/students", headers=student_headers)
    assert r.status_code == 403


def test_student_cannot_access_analytics(student_headers):
    r = client.get("/analytics/dashboard", headers=student_headers)
    assert r.status_code == 403


def test_student_can_access_own_profile(student_headers):
    r = client.get("/student/me", headers=student_headers)
    assert r.status_code == 200
    assert r.json()["student_id"] == "CSE2024001"


def test_dashboard_analytics(faculty_headers):
    r = client.get("/analytics/dashboard", headers=faculty_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["kpis"]["total_students"] > 200
    assert sum(x["value"] for x in data["risk_distribution"]) == data["kpis"]["total_students"]
    assert data["kpis"]["high_risk"] > 0


def test_students_list_pagination(faculty_headers):
    r = client.get("/students?page=1&page_size=5", headers=faculty_headers)
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_students_risk_filter(faculty_headers):
    r = client.get("/students?risk=high&page_size=50", headers=faculty_headers)
    assert r.status_code == 200
    assert all(s["risk_level"] == "high" for s in r.json())


def test_students_search(faculty_headers):
    r = client.get("/students?search=Sanjay", headers=faculty_headers)
    assert r.status_code == 200
    assert all("sanjay" in s["full_name"].lower() for s in r.json())


def test_student_profile_flows(faculty_headers):
    students = client.get("/students?page_size=1", headers=faculty_headers).json()
    sid = students[0]["id"]
    r = client.get(f"/students/{sid}", headers=faculty_headers)
    assert r.status_code == 200
    assert r.json()["id"] == sid
    assert client.get(f"/students/{sid}/performance", headers=faculty_headers).status_code == 200
    assert client.get(f"/students/{sid}/attendance", headers=faculty_headers).status_code == 200
    assert client.get(f"/students/{sid}/engagement", headers=faculty_headers).status_code == 200


def test_prediction_endpoint(faculty_headers):
    students = client.get("/students?page_size=1", headers=faculty_headers).json()
    sid = students[0]["id"]
    r = client.post(
        f"/predictions?student_id={sid}",
        json={
            "attendance": 62.0,
            "previous_performance": 48.0,
            "internal_marks": 51.0,
            "assignment_score": 55.0,
            "engagement": 40.0,
            "study_hours": 2.0,
        },
        headers=faculty_headers,
    )
    assert r.status_code == 200, r.text
    pred = r.json()["prediction"]
    assert 0.0 <= pred["risk_probability"] <= 1.0
    assert pred["risk_level"] in ("low", "moderate", "high")
    assert len(pred["factors"]) == 6
    assert len(pred["recommendations"]) > 0


def test_prediction_validation(faculty_headers):
    students = client.get("/students?page_size=1", headers=faculty_headers).json()
    r = client.post(
        f"/predictions?student_id={students[0]['id']}",
        json={"attendance": 150, "previous_performance": 48, "internal_marks": 51, "assignment_score": 55, "engagement": 40},
        headers=faculty_headers,
    )
    assert r.status_code == 422


def test_dataset_validation_rejects_bad_csv(faculty_headers):
    csv_bytes = "foo,bar\n1,2\n3,4\n".encode()
    r = client.post(
        "/datasets/upload",
        files={"file": ("bad.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"name": "bad"},
        headers=faculty_headers,
    )
    assert r.status_code == 200
    ds = r.json()
    r = client.get(f"/datasets/{ds['id']}/validate", headers=faculty_headers)
    assert r.status_code == 200
    assert len(r.json()["validation_errors"]) > 0


def test_dataset_upload_and_train(faculty_headers):
    df = generate_synthetic_dataset(200)
    csv_bytes = df.to_csv(index=False).encode()
    r = client.post(
        "/datasets/upload",
        files={"file": ("train.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"name": "train"},
        headers=faculty_headers,
    )
    assert r.status_code == 200
    ds = r.json()

    r = client.get(f"/datasets/{ds['id']}/validate", headers=faculty_headers)
    assert r.json()["validation_errors"] == []

    r = client.post("/models/train", json={"dataset_id": ds["id"]}, headers=faculty_headers)
    assert r.status_code == 200, r.text
    result = r.json()
    assert "Random Forest" in result["models"]
    assert "Logistic Regression" in result["models"]
    assert result["best_model"] in ("Random Forest", "Logistic Regression")


def test_model_versioning(faculty_headers):
    r = client.get("/models", headers=faculty_headers)
    assert r.status_code == 200
    models = r.json()
    assert len(models) >= 2
    active = [m for m in models if m["is_active"]]
    assert len(active) == 1
    r = client.get(f"/models/{models[0]['model_id']}", headers=faculty_headers)
    assert r.status_code == 200
    detail = r.json()
    assert len(detail["feature_importance"]) == 6
    assert detail["confusion_matrix"]["matrix"]


def test_intervention_workflow(faculty_headers):
    students = client.get("/students?page_size=1", headers=faculty_headers).json()
    sid = students[0]["id"]
    r = client.post(
        "/interventions",
        json={
            "student_id": sid,
            "type": "mentor_meeting",
            "title": "Test intervention",
            "description": "computed from data",
        },
        headers=faculty_headers,
    )
    assert r.status_code == 200, r.text
    iv = r.json()
    assert iv["type"] == "mentor_meeting"

    r = client.put(f"/interventions/{iv['id']}", json={"status": "in_progress"}, headers=faculty_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"

    r = client.put(f"/interventions/{iv['id']}", json={"status": "completed"}, headers=faculty_headers)
    assert r.status_code == 200
    assert r.json()["completed_date"] is not None

    r = client.post(
        "/interventions",
        json={"student_id": sid, "type": "invalid_type", "title": "x"},
        headers=faculty_headers,
    )
    assert r.status_code == 400


def test_intervention_impact(faculty_headers):
    students = client.get("/students?page_size=1", headers=faculty_headers).json()
    r = client.get(
        f"/analytics/intervention-impact?student_id={students[0]['id']}",
        headers=faculty_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert "intervention_count" in data


def test_reports(faculty_headers):
    students = client.get("/students?page_size=1", headers=faculty_headers).json()
    r = client.get(f"/reports/student/{students[0]['id']}", headers=faculty_headers)
    assert r.status_code == 200
    report = r.json()
    assert report["student"]["name"]
    assert report["academic_health"]["attendance"] is not None


def test_notifications(faculty_headers):
    r = client.get("/notifications", headers=faculty_headers)
    assert r.status_code == 200
    notifs = r.json()
    if notifs:
        r = client.post(f"/notifications/{notifs[0]['id']}/read", headers=faculty_headers)
        assert r.status_code == 200
        assert r.json()["is_read"] is True


def test_authz_student_profile_isolation(student_headers, faculty_headers):
    other = client.get("/students?page_size=1", headers=faculty_headers).json()[0]
    r = client.get(f"/students/{other['id']}", headers=student_headers)
    assert r.status_code == 403


def test_admin_manage_department(admin_headers):
    code = f"TST{int(time.time()) % 100000}"
    r = client.post(
        "/admin/departments",
        json={"name": "Test Dept", "code": code, "description": "testing"},
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    assert r.json()["code"] == code


def test_faculty_cannot_create_department(faculty_headers):
    r = client.post(
        "/admin/departments",
        json={"name": "X", "code": "XX"},
        headers=faculty_headers,
    )
    assert r.status_code == 403