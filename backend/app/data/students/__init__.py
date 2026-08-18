"""Local demo student datasets (Samvidha-style structure).

Each JSON file is one student's full portal dataset. This registry loads all
of them so the seed script and studentRepository can consume them. Replace or
add files here; the schema stays the same so a future college/backend API can
supply the same structure without touching the frontend.
"""
import json
import os

_STUDENTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Public import path for datasets: from app.data.students import PORTAL_DATASETS
PORTAL_DATASETS = []

for fname in sorted(os.listdir(_STUDENTS_DIR)):
    if not (fname.startswith("student") and fname.endswith(".json")):
        continue
    with open(os.path.join(_STUDENTS_DIR, fname), encoding="utf-8") as f:
        PORTAL_DATASETS.append(json.load(f))

__all__ = ["PORTAL_DATASETS"]