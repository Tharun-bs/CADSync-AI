from __future__ import annotations

from pathlib import Path

from src.ai_engine.ml_models import run_ai_analysis
from src.cad_generator.freecad_generator import generate_parametric_cad
from src.drawing_generator.dxf_generator import generate_dxf
from src.excel_parser.parser import parse_excel
from src.knowledge_graph.graph_builder import build_graph
from src.models import PipelineResult
from src.optimization_engine.optimizer import apply_optimized_parameters, optimize_design
from src.report_generator.report_builder import generate_report
from src.utils.config import OUTPUT_ROOT
from src.utils.io_utils import ensure_dir, log_run, write_json
from src.validation_engine.validator import validate_part


def run_pipeline(excel_path: Path, output_root: Path | None = None) -> PipelineResult:
    output_root = output_root or OUTPUT_ROOT
    part = parse_excel(excel_path)

    output_dir = output_root / part.part_id
    ensure_dir(output_dir)

    validation = validate_part(part)
    if not validation.valid:
        log_path = output_dir / "validation_log.json"
        write_json(log_path, {"valid": validation.valid, "errors": validation.errors, "warnings": validation.warnings})
        raise ValueError(f"Validation failed for {part.part_id}. See {log_path}")

    ai_result = run_ai_analysis(part)
    optimization = optimize_design(part)
    optimized_part = apply_optimized_parameters(part, optimization)

    artifacts = generate_parametric_cad(optimized_part, output_dir)
    dxf_path = generate_dxf(optimized_part, artifacts.dxf_path)
    artifacts.dxf_path = dxf_path

    graph_path = build_graph(
        optimized_part,
        validation,
        optimization,
        output_dir / "knowledge_graph.png",
    )

    report_path = generate_report(
        output_dir / "engineering_report.pdf",
        optimized_part,
        validation,
        ai_result,
        optimization,
        artifacts,
        graph_path,
    )

    log_path = output_dir / "validation_log.json"
    write_json(
        log_path,
        {
            "valid": validation.valid,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "ai": {
                "anomaly_score": ai_result.anomaly_score,
                "anomaly_flag": ai_result.anomaly_flag,
                "manufacturability_risk": ai_result.manufacturability_risk,
                "estimated_cost": ai_result.estimated_cost,
            },
            "optimization": optimization.optimized_params,
        },
    )

    log_run(
        part_id=optimized_part.part_id,
        revision=optimized_part.revision,
        valid=validation.valid,
        anomaly_score=ai_result.anomaly_score,
        manufacturability_risk=ai_result.manufacturability_risk,
        estimated_cost=ai_result.estimated_cost,
        output_dir=output_dir,
    )

    return PipelineResult(
        part_spec=optimized_part,
        validation=validation,
        ai_result=ai_result,
        optimization=optimization,
        artifacts=artifacts,
        report_path=report_path,
        graph_path=graph_path,
        log_path=log_path,
    )
