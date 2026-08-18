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
from app.models import (
    User, Dataset, Student, Prediction, Intervention, AssessmentRecord,
    AssignmentRecord, AttendanceRecord, EngagementRecord, AcademicRecord,
)

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=engine)
    _cleanup_import_test_students()
    try:
        r = client.post("/auth/login", json={"username": "admin", "password": "Admin@123"})
        if r.status_code == 200:
            client.post(
                "/admin/data-sources/DEMO/activate",
                headers={"Authorization": f"Bearer {r.json()['access_token']}"},
            )
    except Exception:
        pass
    yield


def _cleanup_import_test_students():
    """Remove students created by CSV import tests so the suite is idempotent."""
    db = SessionLocal()
    try:
        rows = db.query(Student).filter(Student.student_id.like("IMPTEST%")).all()
        if not rows:
            return
        ids = [s.id for s in rows]
        user_ids = [s.user_id for s in rows]
        for model in (Prediction, Intervention, AssessmentRecord, AssignmentRecord,
                      AttendanceRecord, EngagementRecord, AcademicRecord):
            db.query(model).filter(model.student_id.in_(ids)).delete(synchronize_session=False)
        db.query(Student).filter(Student.id.in_(ids)).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        db.query(Dataset).filter(Dataset.name.like("Academic Import%")).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def login(username: str, password: str) -> dict:
    r = client.post("/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def faculty_headers():
    return login("faculty", "Faculty@123")


@pytest.fixture(scope="module")
def admin_headers():
    return login("admin", "Admin@123")


@pytest.fixture(scope="module")
def student_headers():
    return login("student001", "Student@123")


def test_login_rejects_bad_credentials():
    r = client.post("/auth/login", json={"username": "admin", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_rejects_unknown_username():
    r = client.post("/auth/login", json={"username": "no-such-user", "password": "Admin@123"})
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
    assert r.json()["student_id"] == "CSE2026000"


def test_dashboard_analytics(admin_headers):
    r = client.get("/analytics/dashboard", headers=admin_headers)
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


# ----- Personalized academic summaries --------------------------------------------------


def test_student_academic_summary_personalized(student_headers):
    r = client.get("/student/me/academic-summary", headers=student_headers)
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["profile"]["student_id"] == "CSE2026000"
    assert s["health"]["overall_performance"] is not None
    assert len(s["subjects"]) >= 4
    assert s["risk"]["risk_level"] in ("low", "moderate", "high")
    assert len(s["recommendations"]) > 0
    assert s["data_source"]["type"] in ("DEMO", "CSV", "SAMVIDHA")


def test_student_cannot_view_others_summary(student_headers, faculty_headers):
    other = client.get("/students?page_size=1", headers=faculty_headers).json()[0]
    r = client.get(f"/students/{other['id']}/academic-summary", headers=student_headers)
    assert r.status_code == 403


def test_faculty_summary_scoped_to_department(faculty_headers, admin_headers):
    all_sids = client.get("/students?page_size=100", headers=admin_headers).json()
    dept_sids = client.get("/students?page_size=100", headers=faculty_headers).json()
    assert 0 < len(dept_sids) < len(all_sids)


def test_demo_trio_risk_profiles(student_headers):
    import subprocess
    trio = {"student01": "low", "student02": "moderate", "student03": "high"}
    for username, expected in trio.items():
        r = client.post("/auth/login", json={"username": username, "password": "Student@123"})
        assert r.status_code == 200, r.text
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        s = client.get("/student/me/academic-summary", headers=h).json()
        assert s["risk"]["risk_level"] == expected, f"{username}: {s['risk']}"


# ----- Data sources & settings ----------------------------------------------------------


def test_data_source_endpoint(faculty_headers):
    r = client.get("/data-source", headers=faculty_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["type"] in ("DEMO", "CSV", "SAMVIDHA")
    assert data["status"] == "ACTIVE"
    assert data["samvidha_status"] == "NOT_CONFIGURED"


def test_admin_data_sources_list(admin_headers):
    r = client.get("/admin/data-sources", headers=admin_headers)
    assert r.status_code == 200
    sources = r.json()
    types = {s["type"] for s in sources}
    assert {"DEMO", "CSV", "SAMVIDHA"} <= types
    demo = next(s for s in sources if s["type"] == "DEMO")
    assert demo["status"] == "ACTIVE"
    sam = next(s for s in sources if s["type"] == "SAMVIDHA")
    assert sam["status"] == "NOT_CONFIGURED"


def test_admin_cannot_activate_samvidha(admin_headers):
    r = client.post("/admin/data-sources/SAMVIDHA/activate", headers=admin_headers)
    assert r.status_code == 400


def test_data_source_restricted_to_admin(faculty_headers):
    assert client.get("/admin/data-sources", headers=faculty_headers).status_code == 403


def test_risk_threshold_settings(admin_headers):
    r = client.get("/admin/settings", headers=admin_headers)
    assert r.status_code == 200
    settings = {s["key"]: s["value"] for s in r.json()}
    assert "risk_low" in settings and "risk_high" in settings
    r = client.put("/admin/settings/risk_low", json={"value": "0.35"}, headers=admin_headers)
    assert r.status_code == 200
    r = client.put("/admin/settings/risk_high", json={"value": "0.65"}, headers=admin_headers)
    assert r.status_code == 200
    r = client.put("/admin/settings/risk_low", json={"value": "2.0"}, headers=admin_headers)
    assert r.status_code == 400
    r = client.put("/admin/settings/risk_low", json={"value": "0.7"}, headers=admin_headers)
    assert r.status_code == 400
    client.put("/admin/settings/risk_low", json={"value": "0.39"}, headers=admin_headers)
    client.put("/admin/settings/risk_high", json={"value": "0.69"}, headers=admin_headers)


# ----- CSV academic import --------------------------------------------------------------


def _academic_csv_bytes():
    rows = [
        "student_id,student_name,department,section,semester,subject,attendance,internal_1,internal_2,assignment_score,previous_performance,engagement,target",
        "IMPTEST01,Import Test Student,CSE,CSE-A,1,CSE201,82.5,68,72,70,65,62,0",
        "IMPTEST01,Import Test Student,CSE,CSE-A,1,CSE202,79.0,64,66,68,63,58,0",
        "IMPTEST02,Second Test Student,CSE,CSE-A,1,CSE201,48.0,38,35,40,42,30,1",
    ]
    return "\n".join(rows).encode()


def test_import_validate_preview(faculty_headers):
    r = client.post(
        "/datasets/import/validate",
        files={"file": ("academic.csv", io.BytesIO(_academic_csv_bytes()), "text/csv")},
        headers=faculty_headers,
    )
    assert r.status_code == 200, r.text
    rep = r.json()
    assert rep["rows"] == 3
    assert rep["valid_rows"] == 3
    assert rep["rejected"] == 0
    assert rep["imported"] is False
    assert rep["will_create_students"] == 3
    assert len(rep["preview"]) == 3


def test_import_commits_records(faculty_headers, admin_headers):
    _cleanup_import_test_students()
    r = client.post(
        "/datasets/import",
        files={"file": ("academic.csv", io.BytesIO(_academic_csv_bytes()), "text/csv")},
        headers=faculty_headers,
    )
    assert r.status_code == 200, r.text
    res = r.json()
    assert res["imported"] is True
    assert res["imported_rows"] == 3
    assert len(res["created_students"]) == 2
    assert res["source_status"] == "ACTIVE"

    r = client.get("/students?search=IMPTEST&page_size=10", headers=faculty_headers)
    found = [s for s in r.json() if s["student_id"].startswith("IMPTEST")]
    assert len(found) == 2
    sid = found[0]["id"]
    perf = client.get(f"/students/{sid}/performance", headers=faculty_headers)
    assert perf.status_code == 200 and len(perf.json()) >= 1

    client.post("/admin/data-sources/DEMO/activate", headers=admin_headers)


def test_import_history(faculty_headers):
    r = client.get("/datasets/imports/history", headers=faculty_headers)
    assert r.status_code == 200
    assert any(h["status"] == "imported" for h in r.json())


def test_import_rejects_missing_columns(faculty_headers):
    csv_bytes = "student_id,subject\nABC,1\n".encode()
    r = client.post(
        "/datasets/import/validate",
        files={"file": ("bad.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=faculty_headers,
    )
    assert r.status_code == 200
    rep = r.json()
    assert rep["valid_rows"] == 0
    assert len(rep["missing_columns"]) > 0


# ----- Password change ------------------------------------------------------------------


def test_change_password_flow(student_headers):
    r = client.post(
        "/auth/change-password",
        json={"current_password": "wrong", "new_password": "NewPass@123"},
        headers=student_headers,
    )
    assert r.status_code == 400
    r = client.post(
        "/auth/change-password",
        json={"current_password": "Student@123", "new_password": "NewPass@123"},
        headers=student_headers,
    )
    assert r.status_code == 200
    r = client.post("/auth/login", json={"username": "student001", "password": "NewPass@123"})
    assert r.status_code == 200
    r = client.post(
        "/auth/change-password",
        json={"current_password": "NewPass@123", "new_password": "Student@123"},
        headers=student_headers,
    )
    assert r.status_code == 200


def test_notification_dismiss(student_headers):
    notifs = client.get("/notifications", headers=student_headers).json()
    if notifs:
        r = client.post(f"/notifications/{notifs[0]['id']}/dismiss", headers=student_headers)
        assert r.status_code == 200