"""Placeholder for a future official IARE/Samvidha integration.

IMPORTANT
=========
This project is NOT connected to Samvidha and does NOT:
  * scrape or reverse engineer Samvidha
  * bypass authentication
  * automate login with stored Samvidha passwords
  * ask users for their Samvidha password

A real integration requires IARE to provide official API credentials and
documentation. Deply: SAMVIDHA_API_BASE_URL / SAMVIDHA_CLIENT_ID /
SAMVIDHA_CLIENT_SECRET in configuration. Until then the provider stays
NOT_CONFIGURED and raises ProviderNotConfigured for every operation.
"""
from app.providers.base import AcademicDataProvider, ProviderNotConfigured


class SamvidhaAcademicDataProvider(AcademicDataProvider):
    type = "SAMVIDHA"
    display_name = "IARE Samvidha Integration"

    def _require_configured(self):
        src = self.source()
        configured = src is not None and src.status not in ("NOT_CONFIGURED",)
        if not configured:
            raise ProviderNotConfigured(
                "Samvidha integration is not configured. An official IARE API "
                "and credentials are required; no scraping is performed."
            )

    def get_student_profile(self, student_id: int):
        self._require_configured()
        return super().get_student_profile(student_id)

    def get_attendance(self, student_id: int, semester=None):
        self._require_configured()
        return super().get_attendance(student_id, semester)

    def get_academic_records(self, student_id: int, semester=None):
        self._require_configured()
        return super().get_academic_records(student_id, semester)

    def get_assessment_records(self, student_id: int, semester=None):
        self._require_configured()
        return super().get_assessment_records(student_id, semester)

    def get_assignment_records(self, student_id: int, semester=None):
        self._require_configured()
        return super().get_assignment_records(student_id, semester)

    def get_engagement(self, student_id: int, semester=None):
        self._require_configured()
        return super().get_engagement(student_id, semester)

    def get_performance_history(self, student_id: int):
        self._require_configured()
        return super().get_performance_history(student_id)

    def get_class_students(self, faculty_user):
        self._require_configured()
        return super().get_class_students(faculty_user)