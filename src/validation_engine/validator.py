from __future__ import annotations

import re
from itertools import combinations

from src.models import PartSpec, ValidationResult
from src.utils.config import DIMENSION_LIMITS


def _check_limits(name: str, value: float, errors: list[str]) -> None:
    lo, hi = DIMENSION_LIMITS[name]
    if not lo <= value <= hi:
        errors.append(f"{name}={value} is out of bounds [{lo}, {hi}]")


def validate_part(part: PartSpec) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not part.part_id:
        errors.append("Part_ID is missing")

    if not re.match(r"^[A-Z0-9_\-]+$", part.part_id):
        errors.append("Part_ID has invalid naming convention (use A-Z, 0-9, _, -)")

    _check_limits("Length", part.length, errors)
    _check_limits("Width", part.width, errors)
    _check_limits("Height", part.height, errors)
    _check_limits("Hole_Diameter", part.hole_diameter, errors)
    _check_limits("Tolerance", part.tolerance, errors)

    if part.hole_count < 0:
        errors.append("Hole_Count cannot be negative")

    if part.hole_diameter >= min(part.length, part.width):
        errors.append("Hole_Diameter is too large compared to plate footprint")

    if part.hole_count == 0 and part.hole_pattern:
        warnings.append("Hole pattern rows provided but Hole_Count is 0")

    if len(part.hole_pattern) and len(part.hole_pattern) != part.hole_count:
        warnings.append(
            f"Hole_Count={part.hole_count} does not match HolePatterns rows={len(part.hole_pattern)}"
        )

    tol_ratio = part.tolerance / max(part.height, 1e-6)
    if tol_ratio > 0.2:
        errors.append("Tolerance too high for part thickness")

    # Feature overlap check based on simple radius logic.
    points = []
    for idx, hole in enumerate(part.hole_pattern):
        x = float(hole.get("X", 0.0) or 0.0)
        y = float(hole.get("Y", 0.0) or 0.0)
        points.append((idx, x, y))
        if not (0 <= x <= part.length and 0 <= y <= part.width):
            errors.append(f"Hole {idx + 1} position ({x}, {y}) outside plate bounds")

    min_dist = part.hole_diameter + 2 * part.tolerance
    for (i1, x1, y1), (i2, x2, y2) in combinations(points, 2):
        dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if dist < min_dist:
            errors.append(f"Feature overlap risk between hole {i1 + 1} and hole {i2 + 1}")

    if part.length < part.width and part.metadata.get("Orientation", "") == "Landscape":
        warnings.append("Metadata orientation conflicts with geometry proportions")

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)
