"""CSV -> normalized student dataset parser + importer.

CSV → Parser → Normalized Student Model → studentRepository. The frontend
never works directly with CSV columns.
"""
import csv
import io
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models import User, UserRole, Student, Section, Department
from app.repositories.student_repository import upsert_portal_dataset

WEEK_COLS = [f"week{i}" for i in range(1, 15)]


def _f(row: dict, key: str) -> Optional[float]:
    v = row.get(key)
    if v is None or str(v).strip() == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _i(row: dict, key: str) -> Optional[int]:
    v = _f(row, key)
    return int(v) if v is not None else None


def _grade_point(grade: str) -> Optional[int]:
    mapping = {"S": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "C": 5, "D": 4, "F": 0, "-": None}
    return mapping.get(str(grade).strip().upper())


def parse_csv(content: bytes) -> list:
    """Parse CSV bytes into a list of normalized student datasets."""
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV is empty or missing a header row")
    required = {"username", "semester", "courseCode"}
    if not required.issubset(set(reader.fieldnames)):
        missing = required - set(reader.fieldnames)
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

    by_user: dict = {}
    for row in reader:
        username = (row.get("username") or "").strip()
        if not username:
            continue
        if username not in by_user:
            by_user[username] = {
                "username": username,
                "password": row.get("password") or "demo123",
                "name": row.get("name") or username,
                "rollNumber": row.get("rollNumber") or username,
                "studentId": row.get("rollNumber") or username,
                "branch": row.get("branch") or "COMPUTER SCIENCE AND ENGINEERING",
                "regulation": row.get("regulation") or "BT23",
                "section": row.get("section") or "C",
                "year": _i(row, "year") or 1,
                "currentSemester": _i(row, "currentSemester") or 1,
                "cgpa": _f(row, "cgpa"),
                "placeholder": False,
                "semesterRecords": {},
                "currentSemesterCourses": [],
            }
        data = by_user[username]
        sem = _i(row, "semester")
        if sem is None:
            continue
        sem_records = data["semesterRecords"].setdefault(
            sem, {"semester": sem, "theoryCourses": [], "labCourses": [],
                  "attendance": [], "gradeRecords": [], "semesterSummary": {}})
        code = (row.get("courseCode") or "").strip()
        if not code:
            continue
        ctype = str(row.get("courseType") or "T").strip().upper()
        credits = _i(row, "credits")
        grade = row.get("grade") or "-"
        gp = _grade_point(grade)
        attendance = _f(row, "attendance")
        common = {
            "courseCode": code,
            "courseName": row.get("courseName") or code,
            "credits": credits,
            "grade": grade,
            "gradePoint": gp,
            "status": row.get("status") or ("Completed" if gp is not None else "In Progress"),
            "attendance": attendance,
        }
        if ctype in ("L", "LAB", "PRACTICAL"):
            sem_records["labCourses"].append({
                **common, "courseType": "L",
                **{f"week{i}": _f(row, f"week{i}") for i in range(1, 15)},
                "examMarks": _f(row, "examMarks"),
                "totalMarks": _f(row, "totalMarks"),
            })
        else:
            sem_records["theoryCourses"].append({
                **common, "courseType": "T",
                "courseCategory": row.get("courseCategory") or "CORE",
                "CIE1": _f(row, "cie1"), "AAT1_I": _f(row, "aat1_i"),
                "AAT1_II": _f(row, "aat1_ii"), "CIE2": _f(row, "cie2"),
                "AAT2_I": _f(row, "aat2_i"), "AAT2_II": _f(row, "aat2_ii"),
                "totalMarks": _f(row, "totalMarks"),
                "serialNumber": len(sem_records["theoryCourses"]) + 1,
            })
        if attendance is not None:
            sem_records["attendance"].append({
                "courseCode": code, "courseName": row.get("courseName") or code,
                "courseType": ctype if ctype in ("T", "L") else "T",
                "courseCategory": row.get("courseCategory") or "CORE",
                "conducted": None, "attended": None,
                "attendancePercentage": attendance,
                "status": row.get("attendanceStatus") or "",
            })
        if gp is not None or grade == "-":
            sem_records["gradeRecords"].append({
                "courseCode": code, "courseName": row.get("courseName") or code,
                "grade": grade, "gradePoint": gp, "status": common["status"],
                "credits": credits, "attendancePercentage": attendance,
            })

    # Finalize datasets: semester summaries, overall summary, courses due.
    datasets = []
    for username, data in by_user.items():
        records = sorted(data["semesterRecords"].values(), key=lambda s: s["semester"])
        for sr in records:
            sgpa = _compute_sgpa(sr)
            total = sum((c.get("credits") or 0) for c in sr["gradeRecords"] if c.get("gradePoint") is not None)
            sr["semesterSummary"] = {
                "sgpa": sgpa, "totalCredits": total,
                "earnedCredits": total if sgpa is not None else 0,
                "semesterNumber": sr["semester"],
            }
        earned = sum(sr["semesterSummary"]["earnedCredits"] for sr in records)
        data["semesterRecords"] = records
        cur = data["currentSemester"]
        data["currentSemesterCourses"] = [
            {
                "courseCode": c["courseCode"], "courseName": c["courseName"],
                "courseType": c.get("courseType") or "T",
                "courseCategory": c.get("courseCategory") or "CORE",
                "credits": c.get("credits"),
                "attendance": c.get("attendance"),
                "status": c.get("status"),
            }
            for c in (records[-1]["theoryCourses"] + records[-1]["labCourses"])
            if c.get("status") in ("In Progress", "Registered", "-", None)
        ]
        data["overallSummary"] = {
            "cgpa": data.get("cgpa"),
            "totalCredits": earned,
            "earnedCredits": earned,
            "programTotalCredits": 160,
            "currentSemester": cur,
        }
        data["coursesDue"] = _default_courses_due()
        data["profile"] = {
            "name": data["name"], "rollNumber": data["rollNumber"],
            "studentId": data["studentId"], "branch": data["branch"],
            "regulation": data["regulation"], "section": data["section"],
            "year": data["year"], "currentSemester": cur,
            "cgpa": data.get("cgpa"), "previousSgpa": None,
            "previousSemesterCgpa": None, "dateOfAdmission": None,
        }
        datasets.append(data)
    return datasets


def _compute_sgpa(sr: dict) -> Optional[float]:
    points = 0.0
    credits = 0.0
    for c in sr["gradeRecords"]:
        gp = c.get("gradePoint")
        cr = c.get("credits") or 0
        if gp is not None and cr > 0:
            points += gp * cr
            credits += cr
    return round(points / credits, 2) if credits else None


def _default_courses_due() -> list:
    categories = ["FOUNDATION", "CORE", "PROFESSIONAL ELECTIVE", "OPEN ELECTIVE",
                  "PROJECT WORK", "AUDIT", "VALUE ADDED",
                  "FIELD PROJECT / INTERNSHIP", "DIP COURSES"]
    return [{"category": cat, "requiredCourseCount": 0, "registeredCourseCount": 0,
             "yetToBeRegistered": 0} for cat in categories]


def import_datasets(db: Session, datasets: list) -> dict:
    """Persist parsed datasets: create users/students and store portal data."""
    from app.services.base import get_or_create_department, get_or_create_section

    created = []
    for data in datasets:
        username = data["username"]
        user = db.query(User).filter(User.username == username.lower()).first()
        if user is None:
            user = User(username=username.lower(), email=None,
                        hashed_password=get_password_hash(data.get("password") or "demo123"),
                        full_name=data.get("name") or username, role=UserRole.STUDENT)
            db.add(user)
            db.flush()
        student = db.query(Student).filter(Student.student_id == data["rollNumber"]).first()
        if student is None:
            dept = get_or_create_department(db, data["branch"], "CSE")
            section = db.query(Section).filter(
                Section.name == f"CSE-{data.get('section') or 'C'}",
                Section.department_id == dept.id).first()
            if section is None:
                section = get_or_create_section(db, f"CSE-{data.get('section') or 'C'}",
                                                dept, "2025-2026", 1)
            student = Student(
                user_id=user.id, student_id=data["rollNumber"],
                section_id=section.id,
                admission_year=2026 - (data.get("year") or 1),
                current_semester=data.get("currentSemester") or 1,
            )
            db.add(student)
            db.flush()
            created.append(data["rollNumber"])
        upsert_portal_dataset(db, student, data)
    db.commit()
    return {"imported": True, "created_students": created, "students": len(datasets)}