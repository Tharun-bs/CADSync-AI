from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PartSpec:
    part_id: str
    length: float
    width: float
    height: float
    hole_count: int
    hole_diameter: float
    material: str
    tolerance: float
    revision: str
    hole_pattern: list[dict[str, Any]] = field(default_factory=list)
    features: list[dict[str, Any]] = field(default_factory=list)
    configurations: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class AIResult:
    anomaly_score: float
    anomaly_flag: bool
    manufacturability_risk: int
    manufacturability_probability: float
    estimated_cost: float


@dataclass
class OptimizationResult:
    optimized_params: dict[str, float]
    objective_score: float
    notes: list[str] = field(default_factory=list)


@dataclass
class CADArtifacts:
    model_path: Path
    step_path: Path
    iges_path: Path
    stl_path: Path
    dxf_path: Path


@dataclass
class PipelineResult:
    part_spec: PartSpec
    validation: ValidationResult
    ai_result: AIResult
    optimization: OptimizationResult
    artifacts: CADArtifacts
    report_path: Path
    graph_path: Path
    log_path: Path
