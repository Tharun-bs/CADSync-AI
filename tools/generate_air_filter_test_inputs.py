from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUTS_DIR = PROJECT_ROOT / "inputs"
DESCRIPTION_FILE = INPUTS_DIR / "input_descriptions.txt"


def make_hole_pattern(length: float, width: float, hole_count: int, margin: float = 20.0) -> list[dict]:
    if hole_count <= 0:
        return []

    margin_x = min(margin, max(5.0, length * 0.2))
    margin_y = min(margin, max(5.0, width * 0.2))

    x_start = margin_x
    x_end = length - margin_x
    y_start = margin_y
    y_end = width - margin_y

    cols = max(1, math.ceil(math.sqrt(hole_count)))
    rows = max(1, math.ceil(hole_count / cols))

    x_points = [x_start] if cols == 1 else [x_start + i * (x_end - x_start) / (cols - 1) for i in range(cols)]
    y_points = [y_start] if rows == 1 else [y_start + i * (y_end - y_start) / (rows - 1) for i in range(rows)]

    holes: list[dict] = []
    idx = 1
    for y in y_points:
        for x in x_points:
            if idx > hole_count:
                break
            holes.append({"Hole_ID": f"H{idx}", "X": round(x, 3), "Y": round(y, 3)})
            idx += 1

    return holes


def write_case(case: dict, index: int) -> str:
    part_id = case["part_id"]
    filename = f"{index:02d}_{part_id}.xlsx"
    path = INPUTS_DIR / filename

    geometry = pd.DataFrame(
        [
            {
                "Part_ID": part_id,
                "Length": case["length"],
                "Width": case["width"],
                "Height": case["height"],
                "Hole_Count": case["hole_count"],
                "Hole_Diameter": case["hole_diameter"],
                "Material": case["material"],
                "Tolerance": case["tolerance"],
                "Revision": case["revision"],
            }
        ]
    )

    holes = case.get("holes")
    if holes is None:
        holes = make_hole_pattern(case["length"], case["width"], case["hole_count"], case.get("margin", 20.0))

    hole_patterns = pd.DataFrame(holes, columns=["Hole_ID", "X", "Y"])
    feature_rows = [
        {"Feature_Type": "Fillet", "Value": case.get("fillet", 2.0)},
        {"Feature_Type": "Extrusion", "Value": case["height"]},
        {"Feature_Type": "Coating", "Value": case.get("coating", "None")},
    ]
    for key, value in case.get("extra_features", {}).items():
        feature_rows.append({"Feature_Type": key, "Value": value})
    features = pd.DataFrame(feature_rows)
    configurations = pd.DataFrame(
        [
            {
                "Config": "Default",
                "Export_STEP": True,
                "Export_IGES": True,
                "Export_DXF": True,
            }
        ]
    )
    metadata = pd.DataFrame(
        [
            {"Key": "Designer", "Value": "CADSync AI"},
            {"Key": "Project", "Value": "Air Filter Parts Test Suite"},
            {"Key": "Structure_Type", "Value": case.get("structure_type", "plate")},
            {"Key": "Input_Category", "Value": case["category"]},
            {"Key": "Expected_Validation", "Value": case["expected"]},
            {"Key": "Description", "Value": case["description"]},
            {"Key": "Orientation", "Value": case.get("orientation", "Landscape")},
        ]
    )

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        geometry.to_excel(writer, index=False, sheet_name="Geometry")
        hole_patterns.to_excel(writer, index=False, sheet_name="HolePatterns")
        features.to_excel(writer, index=False, sheet_name="Features")
        configurations.to_excel(writer, index=False, sheet_name="Configurations")
        metadata.to_excel(writer, index=False, sheet_name="Metadata")

    return filename


def build_cases() -> list[dict]:
    cases: list[dict] = []

    structure_types = [
        "frame",
        "flange_box",
        "baffle_channel",
        "manifold",
        "cyclone_mount",
        "service_door",
        "cartridge_grid",
    ]

    structure_features = {
        "frame": {"wall_thickness": 12.0},
        "flange_box": {"wall_thickness": 8.0, "wall_height": 10.0},
        "baffle_channel": {"rib_height": 8.0, "rib_thickness": 4.0},
        "manifold": {"boss_diameter": 24.0, "boss_height": 10.0},
        "cyclone_mount": {"central_cutout_diameter": 78.0, "bolt_circle_count": 8},
        "service_door": {
            "window_length": 120.0,
            "window_width": 70.0,
            "hinge_lug_diameter": 12.0,
            "hinge_lug_height": 6.0,
        },
        "cartridge_grid": {
            "rib_height": 7.0,
            "rib_thickness": 3.0,
            "grid_x_count": 4,
            "grid_y_count": 4,
        },
    }

    materials = [
        "Aluminum_6061",
        "Galvanized_Steel",
        "Stainless_304",
        "PowderCoated_Steel",
        "ABS_Polymer",
    ]

    # 1-25: Valid production-style parts with mixed structure types.
    for i in range(1, 26):
        length = 180 + (i * 14)
        width = 120 + (i * 7)
        height = 6 + (i % 8)
        hole_count = [0, 4, 6, 8, 10, 12][i % 6]
        hole_diameter = round(4.0 + (i % 5) * 1.8, 2)
        material = materials[i % len(materials)]
        revision = chr(ord("A") + (i % 3))
        category = "Valid-Production"

        structure_type = structure_types[(i - 1) % len(structure_types)]
        extra_features = dict(structure_features[structure_type])
        if structure_type == "frame":
            extra_features["wall_thickness"] = 8.0 + (i % 4) * 2.0
        if structure_type == "flange_box":
            extra_features["wall_height"] = 8.0 + (i % 5)
        if structure_type == "cartridge_grid":
            extra_features["grid_x_count"] = 3 + (i % 4)
            extra_features["grid_y_count"] = 3 + ((i + 1) % 4)

        cases.append(
            {
                "part_id": f"AF_PANEL_{i:03d}",
                "length": float(length),
                "width": float(width),
                "height": float(height),
                "hole_count": int(hole_count),
                "hole_diameter": float(hole_diameter),
                "material": material,
                "tolerance": round(0.03 + (i % 4) * 0.02, 3),
                "revision": revision,
                "category": category,
                "expected": "PASS",
                "description": f"Standard air-filter panel variant {i} for production baseline testing.",
                "coating": "Zinc" if i % 2 == 0 else "Powder",
                "fillet": 1.5 + (i % 4) * 0.5,
                "structure_type": structure_type,
                "extra_features": extra_features,
            }
        )

    # 26-35: Large/heavy-duty industrial filter parts with complex structures.
    for i in range(26, 36):
        idx = i - 25
        structure_type = structure_types[(i - 1) % len(structure_types)]
        extra_features = dict(structure_features[structure_type])
        if structure_type == "manifold":
            extra_features["boss_diameter"] = 30.0 + (idx % 3) * 4.0
            extra_features["boss_height"] = 12.0 + (idx % 2) * 2.0
        if structure_type == "cyclone_mount":
            extra_features["central_cutout_diameter"] = 120.0 + idx * 4.0
            extra_features["bolt_circle_count"] = 10

        cases.append(
            {
                "part_id": f"AF_HEAVY_{idx:03d}",
                "length": float(900 + idx * 110),
                "width": float(500 + idx * 55),
                "height": float(18 + idx * 2),
                "hole_count": int(12 + idx * 2),
                "hole_diameter": float(10 + (idx % 4) * 2),
                "material": "Stainless_316",
                "tolerance": round(0.08 + (idx % 3) * 0.04, 3),
                "revision": "A",
                "category": "Valid-HeavyDuty",
                "expected": "PASS",
                "description": f"Large industrial filter housing plate {idx} for high-airflow equipment.",
                "coating": "Passivation",
                "fillet": 3.0,
                "structure_type": structure_type,
                "extra_features": extra_features,
            }
        )

    # 36-45: Edge and warning-focused scenarios.
    edge_cases = [
        {
            "part_id": "AF_WARN_001",
            "length": 260.0,
            "width": 210.0,
            "height": 8.0,
            "hole_count": 0,
            "hole_diameter": 8.0,
            "material": "Aluminum_6061",
            "tolerance": 0.05,
            "revision": "A",
            "holes": [{"Hole_ID": "H1", "X": 60.0, "Y": 60.0}],
            "category": "Warning-Mismatch",
            "expected": "PASS_WITH_WARNING",
            "description": "Hole_Count is zero but HolePatterns has rows; tests warning generation.",
            "structure_type": "frame",
            "extra_features": {"wall_thickness": 10.0},
        },
        {
            "part_id": "AF_WARN_002",
            "length": 320.0,
            "width": 140.0,
            "height": 8.0,
            "hole_count": 8,
            "hole_diameter": 8.0,
            "material": "Galvanized_Steel",
            "tolerance": 0.06,
            "revision": "A",
            "holes": make_hole_pattern(320, 140, 6, 18.0),
            "category": "Warning-Mismatch",
            "expected": "PASS_WITH_WARNING",
            "description": "Hole_Count differs from HolePatterns row count to test warning handling.",
            "structure_type": "baffle_channel",
            "extra_features": {"rib_height": 7.0, "rib_thickness": 3.0},
        },
        {
            "part_id": "AF_WARN_003",
            "length": 180.0,
            "width": 300.0,
            "height": 7.0,
            "hole_count": 4,
            "hole_diameter": 6.0,
            "material": "ABS_Polymer",
            "tolerance": 0.04,
            "revision": "B",
            "orientation": "Landscape",
            "category": "Warning-Orientation",
            "expected": "PASS_WITH_WARNING",
            "description": "Width greater than length with Landscape metadata to trigger orientation warning.",
            "structure_type": "service_door",
            "extra_features": {"window_length": 100.0, "window_width": 80.0},
        },
        {
            "part_id": "AF_WARN_004",
            "length": 10.0,
            "width": 10.0,
            "height": 1.0,
            "hole_count": 1,
            "hole_diameter": 0.5,
            "material": "Stainless_304",
            "tolerance": 0.001,
            "revision": "A",
            "holes": [{"Hole_ID": "H1", "X": 5.0, "Y": 5.0}],
            "category": "Boundary-Minimum",
            "expected": "PASS",
            "description": "Lower-bound dimensions and tolerance values for boundary testing.",
            "structure_type": "plate",
        },
        {
            "part_id": "AF_WARN_005",
            "length": 5000.0,
            "width": 5000.0,
            "height": 2000.0,
            "hole_count": 4,
            "hole_diameter": 500.0,
            "material": "Stainless_316",
            "tolerance": 2.0,
            "revision": "A",
            "holes": [
                {"Hole_ID": "H1", "X": 1250.0, "Y": 1250.0},
                {"Hole_ID": "H2", "X": 3750.0, "Y": 1250.0},
                {"Hole_ID": "H3", "X": 1250.0, "Y": 3750.0},
                {"Hole_ID": "H4", "X": 3750.0, "Y": 3750.0},
            ],
            "category": "Boundary-Maximum",
            "expected": "PASS",
            "description": "Upper-bound dimensions and tolerance values for stress and limit testing.",
            "structure_type": "flange_box",
            "extra_features": {"wall_thickness": 120.0, "wall_height": 300.0},
        },
        {
            "part_id": "AF_WARN_006",
            "length": 260.0,
            "width": 180.0,
            "height": 10.0,
            "hole_count": 16,
            "hole_diameter": 6.0,
            "material": "PowderCoated_Steel",
            "tolerance": 0.08,
            "revision": "C",
            "category": "Valid-HighDensity",
            "expected": "PASS",
            "description": "Dense 4x4 hole matrix for airflow and perforation stress testing.",
            "structure_type": "cartridge_grid",
            "extra_features": {"rib_height": 8.0, "rib_thickness": 2.5, "grid_x_count": 4, "grid_y_count": 4},
        },
        {
            "part_id": "AF_WARN_007",
            "length": 420.0,
            "width": 300.0,
            "height": 14.0,
            "hole_count": 24,
            "hole_diameter": 8.0,
            "material": "Galvanized_Steel",
            "tolerance": 0.09,
            "revision": "A",
            "category": "Valid-HighDensity",
            "expected": "PASS",
            "description": "High-count perforated panel case for CNC cycle-time benchmarking.",
            "structure_type": "cyclone_mount",
            "extra_features": {"central_cutout_diameter": 90.0, "bolt_circle_count": 12},
        },
        {
            "part_id": "AF_WARN_008",
            "length": 360.0,
            "width": 260.0,
            "height": 12.0,
            "hole_count": 2,
            "hole_diameter": 20.0,
            "material": "Aluminum_6061",
            "tolerance": 0.05,
            "revision": "A",
            "holes": [
                {"Hole_ID": "H1", "X": 90.0, "Y": 130.0},
                {"Hole_ID": "H2", "X": 270.0, "Y": 130.0},
            ],
            "category": "Valid-LowCount",
            "expected": "PASS",
            "description": "Two-mount-hole bracket style part used for filter frame fixtures.",
            "structure_type": "manifold",
            "extra_features": {"boss_diameter": 26.0, "boss_height": 9.0},
        },
        {
            "part_id": "AF_WARN_009",
            "length": 240.0,
            "width": 240.0,
            "height": 9.0,
            "hole_count": 9,
            "hole_diameter": 7.0,
            "material": "Stainless_304",
            "tolerance": 0.06,
            "revision": "D",
            "category": "Valid-Square",
            "expected": "PASS",
            "description": "Square filter faceplate with 3x3 symmetric perforation pattern.",
            "structure_type": "frame",
            "extra_features": {"wall_thickness": 16.0},
        },
        {
            "part_id": "AF_WARN_010",
            "length": 700.0,
            "width": 160.0,
            "height": 8.0,
            "hole_count": 14,
            "hole_diameter": 5.0,
            "material": "PowderCoated_Steel",
            "tolerance": 0.05,
            "revision": "A",
            "category": "Valid-LongPanel",
            "expected": "PASS",
            "description": "Long narrow cartridge cover panel for duct-mounted air filters.",
            "structure_type": "baffle_channel",
            "extra_features": {"rib_height": 6.0, "rib_thickness": 3.5},
        },
    ]
    cases.extend(edge_cases)

    # 46-50: Invalid scenarios for negative testing.
    invalid_cases = [
        {
            "part_id": "af_invalid_001",
            "length": 220.0,
            "width": 160.0,
            "height": 8.0,
            "hole_count": 4,
            "hole_diameter": 10.0,
            "material": "Aluminum_6061",
            "tolerance": 0.06,
            "revision": "A",
            "category": "Invalid-PartId",
            "expected": "FAIL",
            "description": "Lowercase Part_ID should fail naming convention validation.",
            "structure_type": "service_door",
            "extra_features": {"window_length": 120.0, "window_width": 72.0},
        },
        {
            "part_id": "AF_INVALID_002",
            "length": 250.0,
            "width": 180.0,
            "height": 6.0,
            "hole_count": 2,
            "hole_diameter": 20.0,
            "material": "Stainless_304",
            "tolerance": 1.5,
            "revision": "A",
            "category": "Invalid-ToleranceRatio",
            "expected": "FAIL",
            "description": "Tolerance too high relative to thickness triggers tolerance ratio error.",
            "structure_type": "manifold",
            "extra_features": {"boss_diameter": 22.0, "boss_height": 8.0},
        },
        {
            "part_id": "AF_INVALID_003",
            "length": 200.0,
            "width": 100.0,
            "height": 10.0,
            "hole_count": 2,
            "hole_diameter": 8.0,
            "material": "Galvanized_Steel",
            "tolerance": 0.08,
            "revision": "A",
            "holes": [
                {"Hole_ID": "H1", "X": -5.0, "Y": 30.0},
                {"Hole_ID": "H2", "X": 50.0, "Y": 120.0},
            ],
            "category": "Invalid-HoleBounds",
            "expected": "FAIL",
            "description": "Hole coordinates outside plate bounds to test boundary violations.",
            "structure_type": "cyclone_mount",
            "extra_features": {"central_cutout_diameter": 60.0, "bolt_circle_count": 8},
        },
        {
            "part_id": "AF_INVALID_004",
            "length": 160.0,
            "width": 120.0,
            "height": 8.0,
            "hole_count": 2,
            "hole_diameter": 18.0,
            "material": "PowderCoated_Steel",
            "tolerance": 0.1,
            "revision": "B",
            "holes": [
                {"Hole_ID": "H1", "X": 80.0, "Y": 60.0},
                {"Hole_ID": "H2", "X": 90.0, "Y": 60.0},
            ],
            "category": "Invalid-Overlap",
            "expected": "FAIL",
            "description": "Two holes intentionally too close causing feature overlap risk.",
            "structure_type": "frame",
            "extra_features": {"wall_thickness": 12.0},
        },
        {
            "part_id": "AF_INVALID_005",
            "length": 140.0,
            "width": 90.0,
            "height": 6.0,
            "hole_count": -1,
            "hole_diameter": 5.0,
            "material": "ABS_Polymer",
            "tolerance": 0.04,
            "revision": "A",
            "holes": [],
            "category": "Invalid-NegativeHoleCount",
            "expected": "FAIL",
            "description": "Negative hole count input validates rejection of impossible geometry.",
            "structure_type": "cartridge_grid",
            "extra_features": {"rib_height": 5.0, "rib_thickness": 2.0, "grid_x_count": 3, "grid_y_count": 3},
        },
    ]
    cases.extend(invalid_cases)

    if len(cases) != 50:
        raise RuntimeError(f"Expected exactly 50 cases, found {len(cases)}")

    return cases


def main() -> None:
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)

    cases = build_cases()
    descriptions: list[str] = []

    header = [
        "CADSync AI Air Filter Input Test Suite",
        "Generated set: 50 separate Excel files",
        "Each workbook contains sheets: Geometry, HolePatterns, Features, Configurations, Metadata",
        "",
    ]
    descriptions.extend(header)

    for idx, case in enumerate(cases, start=1):
        filename = write_case(case, idx)
        descriptions.append(
            (
                f"{idx:02d}. {filename} | Category={case['category']} | Expected={case['expected']} | "
                f"Part_ID={case['part_id']} | LxWxH={case['length']}x{case['width']}x{case['height']} mm | "
                f"Structure={case.get('structure_type', 'plate')} | "
                f"Holes={case['hole_count']} x Dia {case['hole_diameter']} mm | Material={case['material']} | "
                f"Tolerance={case['tolerance']} mm | Description={case['description']}"
            )
        )

    DESCRIPTION_FILE.write_text("\n".join(descriptions), encoding="utf-8")

    print(f"Generated {len(cases)} Excel input files in: {INPUTS_DIR}")
    print(f"Descriptions written to: {DESCRIPTION_FILE}")


if __name__ == "__main__":
    main()
