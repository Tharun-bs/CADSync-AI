from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = PROJECT_ROOT / "excel_templates" / "cadsync_template.xlsx"
DEMO_PATH = PROJECT_ROOT / "demo" / "plate_with_holes_demo.xlsx"


def create_template(path: Path) -> None:
    geometry = pd.DataFrame(
        [
            {
                "Part_ID": "PLATE_A100",
                "Length": 220.0,
                "Width": 140.0,
                "Height": 12.0,
                "Hole_Count": 4,
                "Hole_Diameter": 12.0,
                "Material": "Aluminum",
                "Tolerance": 0.08,
                "Revision": "A",
            }
        ]
    )
    hole_patterns = pd.DataFrame(
        [
            {"Hole_ID": "H1", "X": 40.0, "Y": 35.0},
            {"Hole_ID": "H2", "X": 180.0, "Y": 35.0},
            {"Hole_ID": "H3", "X": 40.0, "Y": 105.0},
            {"Hole_ID": "H4", "X": 180.0, "Y": 105.0},
        ]
    )
    features = pd.DataFrame([
        {"Feature_Type": "Fillet", "Value": 3.0},
        {"Feature_Type": "Extrusion", "Value": 12.0},
    ])
    configurations = pd.DataFrame(
        [
            {"Config": "Default", "Export_STEP": True, "Export_IGES": True, "Export_DXF": True},
        ]
    )
    metadata = pd.DataFrame(
        [
            {"Key": "Designer", "Value": "CADSync AI"},
            {"Key": "Project", "Value": "Competition Demo"},
            {"Key": "Orientation", "Value": "Landscape"},
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        geometry.to_excel(writer, index=False, sheet_name="Geometry")
        hole_patterns.to_excel(writer, index=False, sheet_name="HolePatterns")
        features.to_excel(writer, index=False, sheet_name="Features")
        configurations.to_excel(writer, index=False, sheet_name="Configurations")
        metadata.to_excel(writer, index=False, sheet_name="Metadata")


def main() -> None:
    create_template(TEMPLATE_PATH)
    create_template(DEMO_PATH)
    print(f"Template created: {TEMPLATE_PATH}")
    print(f"Demo workbook created: {DEMO_PATH}")


if __name__ == "__main__":
    main()
