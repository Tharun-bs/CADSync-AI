from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.models import PartSpec
from src.utils.config import EXPECTED_SHEETS, GEOMETRY_REQUIRED_COLUMNS


class ExcelSchemaError(ValueError):
    pass


def _validate_workbook_schema(workbook: pd.ExcelFile) -> None:
    sheet_names = set(workbook.sheet_names)
    missing = [name for name in EXPECTED_SHEETS if name not in sheet_names]
    if missing:
        raise ExcelSchemaError(f"Missing required sheets: {missing}")


def parse_excel(file_path: Path) -> PartSpec:
    with pd.ExcelFile(file_path) as workbook:
        _validate_workbook_schema(workbook)

    geometry_df = pd.read_excel(file_path, sheet_name="Geometry")
    if geometry_df.empty:
        raise ExcelSchemaError("Geometry sheet is empty")

    missing_cols = [c for c in GEOMETRY_REQUIRED_COLUMNS if c not in geometry_df.columns]
    if missing_cols:
        raise ExcelSchemaError(f"Geometry sheet missing columns: {missing_cols}")

    row = geometry_df.iloc[0]

    hole_pattern = pd.read_excel(file_path, sheet_name="HolePatterns").fillna("")
    features = pd.read_excel(file_path, sheet_name="Features").fillna("")
    configurations = pd.read_excel(file_path, sheet_name="Configurations").fillna("")
    metadata_df = pd.read_excel(file_path, sheet_name="Metadata").fillna("")

    metadata = {}
    if not metadata_df.empty and {"Key", "Value"}.issubset(metadata_df.columns):
        metadata = {str(r["Key"]): r["Value"] for _, r in metadata_df.iterrows()}

    return PartSpec(
        part_id=str(row["Part_ID"]),
        length=float(row["Length"]),
        width=float(row["Width"]),
        height=float(row["Height"]),
        hole_count=int(row["Hole_Count"]),
        hole_diameter=float(row["Hole_Diameter"]),
        material=str(row["Material"]),
        tolerance=float(row["Tolerance"]),
        revision=str(row["Revision"]),
        hole_pattern=hole_pattern.to_dict(orient="records"),
        features=features.to_dict(orient="records"),
        configurations=configurations.to_dict(orient="records"),
        metadata=metadata,
    )
