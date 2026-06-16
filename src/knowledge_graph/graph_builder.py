from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from src.models import OptimizationResult, PartSpec, ValidationResult


def build_graph(
    part: PartSpec,
    validation: ValidationResult,
    optimization: OptimizationResult,
    out_path: Path,
) -> Path:
    graph = nx.DiGraph()

    part_node = f"Part:{part.part_id}"
    graph.add_node(part_node, kind="part")

    params = {
        "Length": part.length,
        "Width": part.width,
        "Height": part.height,
        "Hole_Count": part.hole_count,
        "Hole_Diameter": part.hole_diameter,
        "Tolerance": part.tolerance,
    }
    for key, value in params.items():
        pnode = f"Param:{key}={value}"
        graph.add_node(pnode, kind="parameter")
        graph.add_edge(part_node, pnode, relation="has_parameter")

    for idx, feat in enumerate(part.features):
        fnode = f"Feature:{idx + 1}:{feat.get('Feature_Type', 'Unknown')}"
        graph.add_node(fnode, kind="feature")
        graph.add_edge(part_node, fnode, relation="has_feature")

    for idx, msg in enumerate(validation.errors + validation.warnings):
        cnode = f"Constraint:{idx + 1}"
        graph.add_node(cnode, kind="constraint", label=msg)
        graph.add_edge(part_node, cnode, relation="constrained_by")

    for key, value in optimization.optimized_params.items():
        onode = f"Optimized:{key}={value}"
        graph.add_node(onode, kind="optimized")
        graph.add_edge(part_node, onode, relation="optimized_to")

    plt.figure(figsize=(14, 10))
    pos = nx.spring_layout(graph, seed=42, k=0.8)
    nx.draw_networkx(
        graph,
        pos=pos,
        with_labels=True,
        font_size=8,
        node_size=950,
        edge_color="#63666A",
        node_color="#B7D3F2",
        arrows=True,
    )
    plt.title(f"CADSync AI Knowledge Graph - {part.part_id}")
    plt.axis("off")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close()
    return out_path
