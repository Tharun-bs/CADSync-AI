from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.models import AIResult, CADArtifacts, OptimizationResult, PartSpec, ValidationResult


def _kv_table(data: dict[str, object]) -> Table:
    rows = [["Key", "Value"]] + [[k, str(v)] for k, v in data.items()]
    table = Table(rows, colWidths=[180, 320])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B4F6C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ]
        )
    )
    return table


def generate_report(
    out_pdf: Path,
    part: PartSpec,
    validation: ValidationResult,
    ai_result: AIResult,
    optimization: OptimizationResult,
    artifacts: CADArtifacts,
    graph_image_path: Path,
) -> Path:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(out_pdf), pagesize=A4)

    content = []
    content.append(Paragraph("CADSync AI Engineering Report", styles["Title"]))
    content.append(Paragraph(f"Part ID: {part.part_id} | Revision: {part.revision}", styles["Heading3"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("Part Summary", styles["Heading2"]))
    content.append(_kv_table(part.to_dict()))
    content.append(Spacer(1, 12))

    content.append(Paragraph("Validation Results", styles["Heading2"]))
    val_map = {
        "Valid": validation.valid,
        "Errors": " | ".join(validation.errors) if validation.errors else "None",
        "Warnings": " | ".join(validation.warnings) if validation.warnings else "None",
    }
    content.append(_kv_table(val_map))
    content.append(Spacer(1, 12))

    content.append(Paragraph("AI Assessment", styles["Heading2"]))
    ai_map = {
        "Anomaly Score": f"{ai_result.anomaly_score:.4f}",
        "Anomaly Flag": ai_result.anomaly_flag,
        "Manufacturability Risk": ai_result.manufacturability_risk,
        "Risk Probability": f"{ai_result.manufacturability_probability:.2%}",
        "Estimated Manufacturing Cost": f"USD {ai_result.estimated_cost}",
    }
    content.append(_kv_table(ai_map))
    content.append(Spacer(1, 12))

    content.append(Paragraph("Optimization Suggestions", styles["Heading2"]))
    content.append(_kv_table(optimization.optimized_params))
    for note in optimization.notes:
        content.append(Paragraph(f"- {note}", styles["BodyText"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("Generated Artifacts", styles["Heading2"]))
    artifacts_map = {
        "STEP": artifacts.step_path,
        "IGES": artifacts.iges_path,
        "STL": artifacts.stl_path,
        "DXF": artifacts.dxf_path,
        "Model": artifacts.model_path,
    }
    content.append(_kv_table({k: str(v) for k, v in artifacts_map.items()}))
    content.append(Spacer(1, 12))

    if graph_image_path.exists():
        content.append(Paragraph("Engineering Knowledge Graph", styles["Heading2"]))
        content.append(Image(str(graph_image_path), width=500, height=360))

    doc.build(content)
    return out_pdf
