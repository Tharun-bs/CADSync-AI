from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from demo.create_demo_excel import create_template
from src.excel_parser.parser import parse_excel
from src.pipeline import run_pipeline
from src.validation_engine.validator import validate_part


class PipelineSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.demo_file = PROJECT_ROOT / "demo" / "test_demo.xlsx"
        create_template(self.demo_file)

    def tearDown(self) -> None:
        if self.demo_file.exists():
            self.demo_file.unlink()

    def test_parse_and_validate(self) -> None:
        part = parse_excel(self.demo_file)
        result = validate_part(part)
        self.assertTrue(result.valid)

    def test_pipeline_generates_outputs(self) -> None:
        result = run_pipeline(self.demo_file)
        self.assertTrue(result.artifacts.step_path.exists())
        self.assertTrue(result.artifacts.iges_path.exists())
        self.assertTrue(result.artifacts.dxf_path.exists())
        self.assertTrue(result.report_path.exists())
        self.assertTrue(result.log_path.exists())


if __name__ == "__main__":
    unittest.main()
