"""Demo academic data provider.

The default provider. Data lives in the application database and was generated
by the seed script from the documented synthetic generator
(backend/app/ml/dataset_generator.py, seed=42). It is clearly labelled as
SYNTHETIC DEMO DATA and must never be presented as real IARE student data.
"""
from app.providers.base import AcademicDataProvider


class DemoAcademicDataProvider(AcademicDataProvider):
    type = "DEMO"
    display_name = "Demo Dataset"

    def get_student_profile(self, student_id: int):
        from app.models import Student
        return self.db.query(Student).filter(Student.id == student_id).first()