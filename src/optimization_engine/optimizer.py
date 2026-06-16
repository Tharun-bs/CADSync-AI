from __future__ import annotations

from dataclasses import replace

import numpy as np
from scipy.optimize import minimize

from src.models import OptimizationResult, PartSpec


def _objective(x: np.ndarray, part: PartSpec) -> float:
    length, width, hole_spacing = x
    base_volume = length * width * part.height
    hole_area = part.hole_count * np.pi * (part.hole_diameter / 2.0) ** 2
    material_use = max(base_volume - hole_area * part.height, 1.0)

    spacing_target = max(part.hole_diameter * 1.8, 8.0)
    spacing_penalty = (hole_spacing - spacing_target) ** 2
    footprint_penalty = 0.001 * ((length - part.length) ** 2 + (width - part.width) ** 2)
    return float(material_use + 1200.0 * spacing_penalty + footprint_penalty)


def _genetic_search(part: PartSpec, generations: int = 40, population: int = 28) -> np.ndarray:
    rng = np.random.default_rng(42)
    pop = np.column_stack(
        [
            rng.uniform(part.length * 0.85, part.length * 1.05, size=population),
            rng.uniform(part.width * 0.85, part.width * 1.05, size=population),
            rng.uniform(part.hole_diameter * 1.3, part.hole_diameter * 4.0, size=population),
        ]
    )

    for _ in range(generations):
        scores = np.array([_objective(candidate, part) for candidate in pop])
        elite_idx = np.argsort(scores)[: population // 2]
        elite = pop[elite_idx]

        children = []
        while len(children) < population - len(elite):
            p1, p2 = elite[rng.integers(0, len(elite), size=2)]
            alpha = rng.uniform(0.2, 0.8)
            child = alpha * p1 + (1 - alpha) * p2
            mutation = rng.normal(0, [2.5, 2.5, 0.6])
            child += mutation
            children.append(child)

        pop = np.vstack([elite, np.array(children)])

    final_scores = np.array([_objective(candidate, part) for candidate in pop])
    return pop[int(np.argmin(final_scores))]


def optimize_design(part: PartSpec) -> OptimizationResult:
    seed = _genetic_search(part)

    bounds = [
        (part.length * 0.8, part.length * 1.1),
        (part.width * 0.8, part.width * 1.1),
        (part.hole_diameter * 1.2, part.hole_diameter * 6.0),
    ]

    result = minimize(_objective, seed, args=(part,), method="L-BFGS-B", bounds=bounds)
    x = result.x if result.success else seed

    optimized_params = {
        "Length": round(float(x[0]), 3),
        "Width": round(float(x[1]), 3),
        "Hole_Spacing": round(float(x[2]), 3),
    }

    return OptimizationResult(
        optimized_params=optimized_params,
        objective_score=round(float(_objective(x, part)), 4),
        notes=[
            "Hybrid optimization executed: GA seed + SciPy refinement.",
            "Objective prioritizes reduced material usage and manufacturable spacing.",
        ],
    )


def apply_optimized_parameters(part: PartSpec, optimized: OptimizationResult) -> PartSpec:
    params = optimized.optimized_params
    return replace(
        part,
        length=float(params["Length"]),
        width=float(params["Width"]),
    )
