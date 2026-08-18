import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import init_db
from app.main import app

# Ensure database tables and base seed data are ready
try:
    init_db()
except Exception:
    pass

__all__ = ["app"]
