from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_pipeline

SHOWCASE_FILE = PROJECT_ROOT / "inputs" / "04_AF_PANEL_004.xlsx"
TEMPLATE_FILE = PROJECT_ROOT / "excel_templates" / "cadsync_template.xlsx"


def _resolve_input_file() -> Path:
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1]).expanduser()
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate

    if SHOWCASE_FILE.exists():
        return SHOWCASE_FILE
    return TEMPLATE_FILE


def main() -> None:
    demo_file = _resolve_input_file()
    if not demo_file.exists():
        raise FileNotFoundError(
            f"Demo workbook not found: {demo_file}. Provide a valid input path or run tools/generate_air_filter_test_inputs.py."
        )

    result = run_pipeline(demo_file)
    print("CADSync AI demo completed successfully")
    print(f"Input workbook: {demo_file}")
    print(f"Part ID: {result.part_spec.part_id}")
    print(f"STEP: {result.artifacts.step_path}")
    print(f"IGES: {result.artifacts.iges_path}")
    print(f"DXF: {result.artifacts.dxf_path}")
    print(f"Report: {result.report_path}")


if __name__ == "__main__":
    main()
