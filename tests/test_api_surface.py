import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_full_api_surface():
    # 1. Login
    r = client.post("/auth/login", json={"email": "faculty@edupredict.local", "password": "Faculty@123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("LOGIN faculty OK")

    # 2. Dashboard analytics
    r = client.get("/analytics/dashboard", headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    print("KPIs:", data["kpis"])
    assert data["kpis"]["total_students"] > 200
    assert len(data["risk_distribution"]) == 3

    # 3. Students list
    r = client.get("/students?page=1&page_size=5", headers=headers)
    assert r.status_code == 200, r.text
    students = r.json()
    assert len(students) <= 5
    print("STUDENTS list OK, first:", students[0]["student_id"], students[0]["full_name"], students[0]["risk_level"])

    # 4. Student detail + performance + attendance
    sid = students[0]["id"]
    r = client.get(f"/students/{sid}", headers=headers)
    assert r.status_code == 200
    r = client.get(f"/students/{sid}/performance", headers=headers)
    assert r.status_code == 200 and len(r.json()) > 0
    r = client.get(f"/students/{sid}/attendance", headers=headers)
    assert r.status_code == 200 and len(r.json()) > 0
    print("STUDENT detail/performance/attendance OK")

    # 5. Model training (using default synthetic dataset uploaded first)
    import io
    from app.ml.dataset_generator import generate_synthetic_dataset
    df = generate_synthetic_dataset(300)
    csv_bytes = df.to_csv(index=False).encode()
    files = {"file": ("demo.csv", io.BytesIO(csv_bytes), "text/csv")}
    r = client.post("/datasets/upload", files=files, data={"name": "demo"}, headers=headers)
    assert r.status_code == 200, r.text
    ds = r.json()
    print("DATASET uploaded:", ds["id"], ds["status"])

    r = client.get(f"/datasets/{ds['id']}/validate", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["validation_errors"] == []
    print("DATASET validate OK, rows:", r.json()["rows"])

    r = client.post("/models/train", json={"dataset_id": ds["id"]}, headers=headers)
    assert r.status_code == 200, r.text
    train_result = r.json()
    print("TRAIN result:", train_result)

    # 6. Prediction on a student
    r = client.post(f"/predictions?student_id={sid}", json={
        "attendance": 62.0, "previous_performance": 48.0, "internal_marks": 51.0,
        "assignment_score": 55.0, "engagement": 40.0, "study_hours": 2.0
    }, headers=headers)
    assert r.status_code == 200, r.text
    pred = r.json()
    print("PREDICTION:", pred["prediction"]["risk_level"], pred["prediction"]["risk_probability"])
    assert "factors" in pred["prediction"] and len(pred["prediction"]["factors"]) == 6
    assert len(pred["prediction"]["recommendations"]) > 0

    # 7. Interventions
    r = client.post("/interventions", json={
        "student_id": sid, "type": "mentor_meeting", "title": "Mentor meeting",
        "description": "Review progress", "follow_up_date": "2026-09-01T00:00:00"
    }, headers=headers)
    assert r.status_code == 200, r.text
    iv = r.json()
    print("INTERVENTION created:", iv["id"])

    r = client.put(f"/interventions/{iv['id']}", json={"status": "in_progress"}, headers=headers)
    assert r.status_code == 200
    print("INTERVENTION updated OK")

    # 8. Models list
    r = client.get("/models", headers=headers)
    assert r.status_code == 200
    models = r.json()
    assert len(models) >= 2, models
    for m in models:
        print(f"  MODEL {m['algorithm']}: acc={m['accuracy']} f1={m['f1_score']} auc={m['roc_auc']} active={m['is_active']}")

    r = client.get(f"/models/{models[0]['model_id']}", headers=headers)
    assert r.status_code == 200
    detail = r.json()
    print("MODEL DETAIL feature importance:", detail["feature_importance"][:2])

    # 9. Notifications
    r = client.get("/notifications", headers=headers)
    assert r.status_code == 200
    print("NOTIFICATIONS:", len(r.json()))

    # 10. Reports
    r = client.get(f"/reports/student/{sid}", headers=headers)
    assert r.status_code == 200, r.text
    rep = r.json()
    print("REPORT generated for", rep["student"]["name"], "recommendations:", len(rep["recommendations"]))

    # 11. Student role isolation
    r = client.post("/auth/login", json={"email": "student@edupredict.local", "password": "Student@123"})
    assert r.status_code == 200
    stoken = r.json()["access_token"]
    sheaders = {"Authorization": f"Bearer {stoken}"}
    r = client.get("/students", headers=sheaders)
    assert r.status_code == 403, r.text
    r = client.get("/analytics/dashboard", headers=sheaders)
    assert r.status_code == 403
    r = client.get("/student/me", headers=sheaders)
    assert r.status_code == 200
    me = r.json()
    print("STUDENT self:", me["student_id"], "risk:", me["risk_level"])
    # student trying to access another student
    other = client.get("/students", headers=headers).json()[0]
    r = client.get(f"/students/{other['id']}", headers=sheaders)
    assert r.status_code == 403 if other["id"] != me["id"] else 200
    print("ROLE ISOLATION OK")

    # 12. Intervention impact
    r = client.get(f"/analytics/intervention-impact?student_id={sid}", headers=headers)
    assert r.status_code == 200, r.text
    print("IMPACT:", r.json())

    print("\nALL API TESTS PASSED")


if __name__ == "__main__":
    test_full_api_surface()
