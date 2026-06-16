from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = PROJECT_ROOT / "outputs"
MODEL_ROOT = PROJECT_ROOT / "models"
DATA_ROOT = PROJECT_ROOT / "data"
TEMPLATE_ROOT = PROJECT_ROOT / "excel_templates"
DB_PATH = DATA_ROOT / "cadsync_runs.db"

EXPECTED_SHEETS = [
    "Geometry",
    "HolePatterns",
    "Features",
    "Configurations",
    "Metadata",
]

GEOMETRY_REQUIRED_COLUMNS = [
    "Part_ID",
    "Length",
    "Width",
    "Height",
    "Hole_Count",
    "Hole_Diameter",
    "Material",
    "Tolerance",
    "Revision",
]

DIMENSION_LIMITS = {
    "Length": (10.0, 5000.0),
    "Width": (10.0, 5000.0),
    "Height": (1.0, 2000.0),
    "Hole_Diameter": (0.5, 500.0),
    "Tolerance": (0.001, 2.0),
}
