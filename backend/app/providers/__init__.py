"""Academic data provider abstraction.

EduPredict does NOT depend on a particular academic data source. The
frontend/backend talk to an AcademicDataProvider, and the active provider is
selected at runtime from the data_sources table (admin switchable):

  - DemoAcademicDataProvider   (DEMO,      default, synthetic seeded data)
  - CsvAcademicDataProvider    (CSV,       approved academic CSV imports)
  - SamvidhaAcademicDataProvider (SAMVIDHA, NOT_CONFIGURED until an official
    IARE/Samvidha API is provided — never scraped or reverse engineered)
"""

from app.providers.base import (
    AcademicDataProvider,
    ProviderNotConfigured,
    get_active_provider,
    activate_data_source,
    list_data_sources,
    ensure_default_sources,
)
from app.providers.demo_provider import DemoAcademicDataProvider
from app.providers.csv_provider import CsvAcademicDataProvider
from app.providers.samvidha_provider import SamvidhaAcademicDataProvider

PROVIDER_BY_TYPE = {
    "DEMO": DemoAcademicDataProvider,
    "CSV": CsvAcademicDataProvider,
    "SAMVIDHA": SamvidhaAcademicDataProvider,
}

__all__ = [
    "AcademicDataProvider",
    "ProviderNotConfigured",
    "DemoAcademicDataProvider",
    "CsvAcademicDataProvider",
    "SamvidhaAcademicDataProvider",
    "PROVIDER_BY_TYPE",
    "get_active_provider",
    "activate_data_source",
    "list_data_sources",
    "ensure_default_sources",
]