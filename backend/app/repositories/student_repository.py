"""Student repository.

This is the ONLY place the application reads student data from storage.
It supports MongoDB storage and falls back to SQLite/JSON storage seamlessly.
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from app.models import PortalDataset, Student
from app.core.mongodb import get_portal_datasets_collection


def get_portal_dataset(db: Session, student: Student) -> Optional[dict]:
    """Return the student's full Samvidha-style dataset as a dict (or None).

    Checks MongoDB portal_datasets collection first; falls back to SQLite storage.
    """
    # 1. Check MongoDB
    mongo_col = get_portal_datasets_collection()
    if mongo_col is not None:
        try:
            doc = mongo_col.find_one(
                {"$or": [{"studentId": student.student_id}, {"rollNumber": student.student_id}, {"username": student.user.username}]}
            )
            if doc is not None:
                doc.pop("_id", None)
                return doc
        except Exception:
            pass

    # 2. Fall back to SQLite storage
    row = db.query(PortalDataset).filter(PortalDataset.student_id == student.id).first()
    if row is None:
        return None
    return json.loads(row.data)


def upsert_portal_dataset(db: Session, student: Student, data: dict) -> PortalDataset:
    """Save/update portal dataset in both MongoDB (if connected) and SQLite."""
    # 1. Sync to MongoDB if connected
    mongo_col = get_portal_datasets_collection()
    if mongo_col is not None:
        try:
            mongo_col.update_one(
                {"studentId": student.student_id},
                {"$set": data},
                upsert=True,
            )
        except Exception:
            pass

    # 2. Sync to SQLite
    row = db.query(PortalDataset).filter(PortalDataset.student_id == student.id).first()
    if row is None:
        row = PortalDataset(student_id=student.id, data=json.dumps(data))
        db.add(row)
    else:
        row.data = json.dumps(data)
    db.flush()
    return row


def student_for_user(db: Session, user_id: int) -> Optional[Student]:
    return db.query(Student).filter(Student.user_id == user_id).first()