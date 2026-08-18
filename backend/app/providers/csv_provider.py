"""CSV academic data provider.

Imports approved academic CSV exports into the application database (with
validation + preview) and serves them through the standard provider surface.
The column mapping is configurable, with a sensible default for the
documented format.
"""
import pandas as pd

from app.providers.base import AcademicDataProvider


# Default mapping: documented CSV columns -> application fields.
# Aliases are accepted (e.g. internal_1 / internal1, assignment / assignment_score).
DEFAULT_COLUMN_MAP = {
    "student_id": ["student_id", "roll_number", "roll_no", "id"],
    "student_name": ["student_name", "name", "full_name"],
    "department": ["department", "dept", "department_code"],
    "section": ["section", "section_name"],
    "semester": ["semester", "sem"],
    "subject": ["subject", "subject_name", "subject_code"],
    "attendance": ["attendance", "attendance_percentage", "attendance_pct"],
    "internal_1": ["internal_1", "internal1", "internal_i", "internal_marks_1"],
    "internal_2": ["internal_2", "internal2", "internal_ii", "internal_marks_2"],
    "assignment_score": ["assignment_score", "assignment", "assignments"],
    "previous_performance": ["previous_performance", "previous_gpa", "gpa", "cgpa"],
    "engagement": ["engagement", "engagement_score"],
    "target": ["target", "at_risk", "risk_label"],
}

REQUIRED_FIELDS = ["student_id", "subject", "semester"]


class CsvAcademicDataProvider(AcademicDataProvider):
    type = "CSV"
    display_name = "Approved Academic Import"

    # ----- reading (same database surface as the demo provider) -----------------
    def get_student_profile(self, student_id: int):
        from app.models import Student
        return self.db.query(Student).filter(Student.id == student_id).first()

    def find_student_by_external_id(self, external_id: str):
        from app.models import Student
        return self.db.query(Student).filter(Student.student_id == external_id).first()

    # ----- column resolution -----------------------------------------------------
    def _resolve_columns(self, cols: list, mapping: dict) -> dict:
        resolved = {}
        for field, candidates in DEFAULT_COLUMN_MAP.items():
            alias = mapping.get(field)
            if alias and alias in cols:
                resolved[field] = alias
                continue
            for c in candidates:
                if c in cols:
                    resolved[field] = c
                    break
        for field, alias in (mapping or {}).items():
            if alias in cols and field not in resolved:
                resolved[field] = alias
        return resolved

    # ----- validation -------------------------------------------------------------
    @staticmethod
    def _error_lines(errors: list) -> list:
        return [f"Row {e['row']}: {e['reason']}" for e in errors[:50]]

    def _validate_row(self, row: dict, data_row_index: int, errors: list, warnings: list,
                      subjects_lookup: dict) -> dict:
        for f in REQUIRED_FIELDS:
            val = row.get(f)
            if val is None or (isinstance(val, str) and not val.strip()):
                errors.append({"row": data_row_index + 2, "reason": f"Missing required column '{f}'"})
                return None

        student_id = str(row["student_id"]).strip()
        subject = str(row["subject"]).strip()
        semester = row.get("semester")
        try:
            semester = int(float(semester))
            if semester < 1 or semester > 8:
                errors.append({"row": data_row_index + 2, "reason": f"Invalid semester: {semester}"})
                return None
        except (TypeError, ValueError):
            errors.append({"row": data_row_index + 2, "reason": f"Invalid semester: {semester!r}"})
            return None

        if subject.lower() not in subjects_lookup:
            errors.append({"row": data_row_index + 2, "reason": f"Unknown subject: {subject}"})
            return None

        def num(field):
            v = row.get(field)
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        checks = {
            "attendance": (0, 100), "internal_1": (0, 100), "internal_2": (0, 100),
            "assignment_score": (0, 100), "previous_performance": (0, 100),
            "engagement": (0, 100),
        }
        cleaned = {"student_id": student_id, "subject": subject, "semester": semester,
                   "student_name": None, "department": None, "section": None}
        for field, (lo, hi) in checks.items():
            v = num(field)
            if v is not None:
                if v < lo or v > hi:
                    errors.append({"row": data_row_index + 2, "reason": f"{field} out of range: {v}"})
                    return None
                cleaned[field] = round(v, 2)
            else:
                warnings.append({"row": data_row_index + 2, "reason": f"{field} missing (stored as null)"})
                cleaned[field] = None

        for f in ("student_name", "department", "section"):
            v = row.get(f)
            cleaned[f] = str(v).strip() if v is not None else None
        return cleaned

    def validate_import(self, df: pd.DataFrame, mapping: dict | None = None,
                        resolved: dict | None = None) -> dict:
        """Validation report (preview). Does NOT import anything."""
        from app.models import Subject
        cols = list(df.columns)
        if resolved is None:
            resolved = self._resolve_columns(cols, mapping or {})
        missing = [f for f in REQUIRED_FIELDS if f not in resolved]
        if missing:
            return {
                "rows": len(df), "valid_rows": 0, "warnings": [],
                "rejected": len(df),
                "errors": [{"row": 1, "reason": f"Missing required columns: {', '.join(missing)}"}],
                "preview": [], "missing_columns": missing, "column_map": {},
                "will_create_students": 0, "imported": False, "valid_records": [],
            }

        subjects_lookup = {}
        for s in self.db.query(Subject).all():
            subjects_lookup[s.code.lower()] = s
            subjects_lookup[s.name.lower()] = s
        errors, warnings, cleaned_rows, seen = [], [], [], set()
        for idx, raw in enumerate(df.to_dict(orient="records")):
            row = {f: raw.get(alias) for f, alias in resolved.items()}
            dup_key = (str(row.get("student_id", "")).strip(), str(row.get("subject", "")).strip(),
                       str(row.get("semester", "")).strip(), str(row.get("internal_1", "")).strip())
            if dup_key in seen:
                errors.append({"row": idx + 2, "reason": "Duplicate record"})
                continue
            seen.add(dup_key)
            cleaned = self._validate_row(row, idx, errors, warnings, subjects_lookup)
            if cleaned is not None:
                cleaned_rows.append(cleaned)

        from app.models import Student
        existing_ids = {s.student_id for s in self.db.query(Student.student_id).all()}
        final_records, will_create = [], 0
        for c in cleaned_rows:
            if c["student_id"] not in existing_ids:
                if not c.get("student_name"):
                    errors.append({"row": 0, "reason": f"Unknown student ID '{c['student_id']}' (no student_name to create record)"})
                    continue
                will_create += 1
            final_records.append(c)

        return {
            "rows": len(df), "valid_rows": len(final_records), "warnings": warnings,
            "rejected": len(errors), "errors": self._error_lines(errors),
            "errors_total": len(errors), "error_truncated": len(errors) > 50,
            "preview": final_records[:10], "missing_columns": [], "column_map": resolved,
            "will_create_students": will_create, "imported": False,
            "valid_records": final_records,
        }

    # ----- import -----------------------------------------------------------------
    def import_records(self, df: pd.DataFrame, mapping: dict | None = None,
                       report: dict | None = None) -> dict:
        """Import valid rows into the database and activate the CSV source."""
        from datetime import datetime
        from app.models import (
            AcademicRecord, AssessmentRecord, AssignmentRecord, AttendanceRecord,
            Department, EngagementRecord, Section, Student, Subject, User,
            UserRole, DataSource,
        )

        if report is None or report.get("valid_records") is None:
            report = self.validate_import(df, mapping)
        valid_rows = report.get("valid_records", [])
        if not valid_rows:
            err = report["errors"]
            raise ValueError(err[0] if err else "No valid records to import")

        subjects_lookup = {}
        for s in self.db.query(Subject).all():
            subjects_lookup[s.code.lower()] = s
            subjects_lookup[s.name.lower()] = s
        depts_lookup = {d.code.lower(): d for d in self.db.query(Department).all()}
        students_by_id = {s.student_id: s for s in self.db.query(Student).all()}
        created_students = []

        def _ensure_section(dept_code: str, sec_name: str | None, semester: int) -> Section:
            dept = depts_lookup.get((dept_code or "CSE").lower())
            if dept is None:
                dept = self.db.query(Department).filter(Department.code == "CSE").first()
            name = (sec_name or f"{dept.code}-A").upper()
            section = self.db.query(Section).filter(
                Section.name == name, Section.department_id == dept.id,
                Section.semester == semester,
            ).first()
            if section is None:
                section = self.db.query(Section).filter(
                    Section.name == f"{dept.code}-A", Section.semester == 1,
                ).first()
            return section

        for c in valid_rows:
            student = students_by_id.get(c["student_id"])
            if student is None:
                section = _ensure_section(c.get("department"), c.get("section"), c["semester"])
                hashed = self.db.query(User.hashed_password).filter(
                    User.username == f"u{c['student_id'].lower()}"
                ).first()
                user = User(
                    username=f"u{c['student_id'].lower()}",
                    hashed_password="!",  # placeholder; admin must set a password
                    full_name=c.get("student_name") or c["student_id"],
                    role=UserRole.STUDENT,
                )
                self.db.add(user)
                self.db.flush()
                student = Student(
                    user_id=user.id, student_id=c["student_id"],
                    section_id=section.id, admission_year=2025,
                    current_semester=c["semester"],
                )
                self.db.add(student)
                self.db.flush()
                students_by_id[c["student_id"]] = student
                created_students.append(c["student_id"])

            sid, sem = student.id, c["semester"]
            subject = subjects_lookup[c["subject"].lower()]

            i1, i2 = c.get("internal_1"), c.get("internal_2")
            internal = None
            if i1 is not None or i2 is not None:
                internal = round(((i1 or 0) + (i2 or 0)) / 2, 1)
            total = None
            if internal is not None:
                assign = c.get("assignment_score") or internal
                total = round(min(0.5 * internal + 0.3 * assign + 0.2 * internal, 100), 1)

            ac = self.db.query(AcademicRecord).filter(
                AcademicRecord.student_id == sid, AcademicRecord.subject_id == subject.id,
                AcademicRecord.semester == sem,
            ).first()
            if ac is None:
                ac = AcademicRecord(student_id=sid, subject_id=subject.id, semester=sem)
                self.db.add(ac)
            ac.internal_marks = internal
            ac.assignment_score = c.get("assignment_score")
            ac.total_score = total
            ac.grade = ("A" if total >= 80 else "B" if total >= 65 else "C" if total >= 50
                        else "D" if total >= 40 else "F") if total is not None else None

            for num, key in ((1, "internal_1"), (2, "internal_2")):
                if c.get(key) is not None:
                    ar = self.db.query(AssessmentRecord).filter(
                        AssessmentRecord.student_id == sid, AssessmentRecord.subject_id == subject.id,
                        AssessmentRecord.semester == sem, AssessmentRecord.assessment_number == num,
                    ).first()
                    if ar is None:
                        ar = AssessmentRecord(student_id=sid, subject_id=subject.id,
                                              semester=sem, assessment_number=num, marks=c[key])
                        self.db.add(ar)
                    else:
                        ar.marks = c[key]

            aw = self.db.query(AssignmentRecord).filter(
                AssignmentRecord.student_id == sid, AssignmentRecord.subject_id == subject.id,
                AssignmentRecord.semester == sem,
            ).first()
            if aw is None:
                aw = AssignmentRecord(student_id=sid, subject_id=subject.id, semester=sem)
                self.db.add(aw)
            aw.score = c.get("assignment_score")
            aw.completion_percentage = c.get("assignment_score")

            at = self.db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == sid, AttendanceRecord.subject_id == subject.id,
                AttendanceRecord.semester == sem,
            ).order_by(AttendanceRecord.month.desc()).first()
            if at is None:
                at = AttendanceRecord(student_id=sid, subject_id=subject.id, semester=sem, month=8)
                self.db.add(at)
            at.classes_held = 30
            at.classes_attended = int(round(30 * (c["attendance"] / 100))) if c.get("attendance") is not None else 30
            at.attendance_percentage = c.get("attendance")

            eg = self.db.query(EngagementRecord).filter(
                EngagementRecord.student_id == sid, EngagementRecord.semester == sem,
            ).order_by(EngagementRecord.month.desc()).first()
            if eg is None:
                eg = EngagementRecord(student_id=sid, semester=sem, month=8)
                self.db.add(eg)
            eg.engagement_score = c.get("engagement")
            eg.participation_score = c.get("engagement")
            self.db.flush()

        src = self.db.query(DataSource).filter(DataSource.type == "CSV").first()
        if src:
            for other in self.db.query(DataSource).filter(DataSource.status == "ACTIVE").all():
                other.status = "AVAILABLE"
            src.status = "ACTIVE"
            src.last_synced_at = datetime.utcnow()
            src.record_count = self.db.query(Student).count()

        self.db.commit()
        return {
            "imported_rows": len(valid_rows),
            "created_students": sorted(created_students),
            "source_status": "ACTIVE",
            "rows": report["rows"], "valid_rows": len(valid_rows),
            "warnings": report["warnings"][:20], "rejected": report["errors_total"],
            "imported": True,
        }