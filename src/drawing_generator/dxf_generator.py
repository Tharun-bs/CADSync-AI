from __future__ import annotations

from pathlib import Path

from src.models import PartSpec


def _add_dimension(msp, x1: float, y1: float, x2: float, y2: float, value: str, layer: str = "Dimensions") -> None:
    """Add a dimension line with annotation."""
    msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": layer, "color": 5})
    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
    msp.add_text(value, dxfattribs={"height": 2.5, "layer": layer}).set_pos((mid_x - 3, mid_y + 1))


def generate_dxf(part: PartSpec, dxf_path: Path) -> Path:
    """Generate a professional manufacturing drawing with 25-30 dimensions and annotations."""
    try:
        import ezdxf
    except ImportError:
        raise ImportError("ezdxf required for professional DXF generation. Install: pip install ezdxf")

    dxf = ezdxf.new("R2010")
    msp = dxf.modelspace()

    # === SETUP LAYERS ===
    dxf.layers.new(name="Geometry", dxfattribs={"color": 7})
    dxf.layers.new(name="Dimensions", dxfattribs={"color": 5})
    dxf.layers.new(name="HolePattern", dxfattribs={"color": 3})
    dxf.layers.new(name="Annotations", dxfattribs={"color": 1})
    dxf.layers.new(name="TitleBlock", dxfattribs={"color": 1})

    # === TOP VIEW (Main) ===
    # Outline rectangle
    msp.add_lwpolyline(
        [(0, 0), (part.length, 0), (part.length, part.width), (0, part.width), (0, 0)],
        dxfattribs={"layer": "Geometry", "color": 7},
    )

    # === HOLE PATTERN ===
    radius = part.hole_diameter / 2.0
    for idx, hole in enumerate(part.hole_pattern):
        x = float(hole.get("X", part.length / 2.0))
        y = float(hole.get("Y", part.width / 2.0))
        msp.add_circle((x, y), radius, dxfattribs={"layer": "HolePattern", "color": 3})
        msp.add_text(f"H{idx + 1}", dxfattribs={"height": 2.0, "layer": "HolePattern"}).set_dxf_attrib("insert", (x + radius + 1, y))

    # === OVERALL DIMENSIONS ===
    # Length dimension (bottom)
    msp.add_line((0, -8), (part.length, -8), dxfattribs={"layer": "Dimensions", "color": 5})
    msp.add_line((0, -6), (0, -10), dxfattribs={"layer": "Dimensions", "color": 5})
    msp.add_line((part.length, -6), (part.length, -10), dxfattribs={"layer": "Dimensions", "color": 5})
    msp.add_text(
        f"{part.length} mm", dxfattribs={"height": 2.5, "layer": "Dimensions", "insert": (part.length / 2.0 - 8, -12)}
    )

    # Width dimension (left)
    msp.add_line((-8, 0), (-8, part.width), dxfattribs={"layer": "Dimensions", "color": 5})
    msp.add_line((-6, 0), (-10, 0), dxfattribs={"layer": "Dimensions", "color": 5})
    msp.add_line((-6, part.width), (-10, part.width), dxfattribs={"layer": "Dimensions", "color": 5})
    msp.add_text(
        f"{part.width} mm", dxfattribs={"height": 2.5, "layer": "Dimensions", "insert": (-20, part.width / 2.0)}
    )

    # === HOLE SPECIFIC DIMENSIONS ===
    msp.add_text(
        f"Hole Dia: φ{part.hole_diameter} mm ±{part.tolerance} mm",
        dxfattribs={"height": 2.2, "layer": "Dimensions", "insert": (part.length + 10, part.width - 5)},
    )
    msp.add_text(
        f"Hole Count: {part.hole_count}",
        dxfattribs={"height": 2.2, "layer": "Dimensions", "insert": (part.length + 10, part.width - 10)},
    )

    # Hole pattern table with individual hole positions
    table_x = 0
    table_y = part.width + 15
    msp.add_text("HOLE PATTERN TABLE", dxfattribs={"height": 2.5, "layer": "Annotations", "insert": (table_x, table_y)})

    for idx, hole in enumerate(part.hole_pattern[:25]):
        x = float(hole.get("X", part.length / 2.0))
        y = float(hole.get("Y", part.width / 2.0))
        msp.add_text(
            f"H{idx + 1}: X={x:.2f} Y={y:.2f}",
            dxfattribs={"height": 1.8, "layer": "Annotations", "insert": (table_x, table_y - 5 - (idx * 3))},
        )

    # === PART INFORMATION BLOCK ===
    info_x = part.length + 15
    info_y = part.width + 20
    msp.add_text("PART INFORMATION", dxfattribs={"height": 2.8, "layer": "TitleBlock", "insert": (info_x, info_y)})
    info_y -= 5
    msp.add_text(f"Part ID: {part.part_id}", dxfattribs={"height": 2.2, "layer": "TitleBlock", "insert": (info_x, info_y)})
    info_y -= 4
    msp.add_text(
        f"Revision: {part.revision}", dxfattribs={"height": 2.2, "layer": "TitleBlock", "insert": (info_x, info_y)}
    )
    info_y -= 4
    msp.add_text(f"Material: {part.material}", dxfattribs={"height": 2.2, "layer": "TitleBlock", "insert": (info_x, info_y)})
    info_y -= 4
    msp.add_text(
        f"Tolerance: ±{part.tolerance} mm",
        dxfattribs={"height": 2.2, "layer": "TitleBlock", "insert": (info_x, info_y)},
    )
    info_y -= 4
    msp.add_text(f"Thickness: {part.height} mm", dxfattribs={"height": 2.2, "layer": "TitleBlock", "insert": (info_x, info_y)})

    # === TOLERANCES & GD&T ===
    gdt_y = info_y - 8
    msp.add_text("TOLERANCES & GD&T", dxfattribs={"height": 2.4, "layer": "Annotations", "insert": (info_x, gdt_y)})
    gdt_y -= 4
    msp.add_text(
        f"Linear Tolerance: ±{part.tolerance} mm",
        dxfattribs={"height": 2.0, "layer": "Annotations", "insert": (info_x, gdt_y)},
    )
    gdt_y -= 3
    msp.add_text(
        f"Hole Tolerance: H7 (φ{part.hole_diameter})",
        dxfattribs={"height": 2.0, "layer": "Annotations", "insert": (info_x, gdt_y)},
    )
    gdt_y -= 3
    msp.add_text(
        "Flatness: 0.05 mm (ALL SURFACES)",
        dxfattribs={"height": 2.0, "layer": "Annotations", "insert": (info_x, gdt_y)},
    )
    gdt_y -= 3
    msp.add_text(
        "Perpendicularity: 0.10 mm",
        dxfattribs={"height": 2.0, "layer": "Annotations", "insert": (info_x, gdt_y)},
    )

    # === DATUM REFERENCES ===
    datum_y = gdt_y - 6
    msp.add_text("DATUM REFERENCES", dxfattribs={"height": 2.4, "layer": "Annotations", "insert": (info_x, datum_y)})
    datum_y -= 4
    msp.add_text(
        "Datum A: Bottom face", dxfattribs={"height": 2.0, "layer": "Annotations", "insert": (info_x, datum_y)}
    )
    datum_y -= 3
    msp.add_text("Datum B: Left edge", dxfattribs={"height": 2.0, "layer": "Annotations", "insert": (info_x, datum_y)})
    datum_y -= 3
    msp.add_text("Datum C: Front edge", dxfattribs={"height": 2.0, "layer": "Annotations", "insert": (info_x, datum_y)})

    # === FEATURES & NOTES ===
    notes_y = part.width + 10 + 100
    msp.add_text(
        "MANUFACTURING NOTES", dxfattribs={"height": 2.4, "layer": "Annotations", "insert": (table_x, notes_y)}
    )
    notes_y -= 5
    msp.add_text(
        f"1. All dimensions in millimeters unless otherwise specified",
        dxfattribs={"height": 1.9, "layer": "Annotations", "insert": (table_x, notes_y)},
    )
    notes_y -= 3
    msp.add_text(
        f"2. Material: {part.material} alloy per ASTM standards",
        dxfattribs={"height": 1.9, "layer": "Annotations", "insert": (table_x, notes_y)},
    )
    notes_y -= 3
    msp.add_text(
        f"3. Break all sharp edges with 0.5 mm chamfer or fillet",
        dxfattribs={"height": 1.9, "layer": "Annotations", "insert": (table_x, notes_y)},
    )
    notes_y -= 3
    msp.add_text(
        f"4. Surface finish: Ra 1.6 µm on all machined surfaces",
        dxfattribs={"height": 1.9, "layer": "Annotations", "insert": (table_x, notes_y)},
    )
    notes_y -= 3
    msp.add_text(
        f"5. Hole drilling sequence: Center → pilot → finish",
        dxfattribs={"height": 1.9, "layer": "Annotations", "insert": (table_x, notes_y)},
    )
    notes_y -= 3
    msp.add_text(
        f"6. Deburr and remove all swarf after machining",
        dxfattribs={"height": 1.9, "layer": "Annotations", "insert": (table_x, notes_y)},
    )

    # === REVISION HISTORY ===
    revision_x = info_x
    revision_y = datum_y - 10
    msp.add_text(
        "REVISION HISTORY", dxfattribs={"height": 2.2, "layer": "TitleBlock", "insert": (revision_x, revision_y)}
    )
    revision_y -= 4
    msp.add_text(
        f"Rev {part.revision}: Initial release - CADSync AI Gen",
        dxfattribs={"height": 1.9, "layer": "TitleBlock", "insert": (revision_x, revision_y)},
    )

    # === FRONT VIEW (Side elevation schematic) ===
    front_x = part.length + 30
    front_y = 0
    msp.add_lwpolyline(
        [(front_x, front_y), (front_x + 40, front_y), (front_x + 40, front_y + part.height), (front_x, front_y + part.height), (front_x, front_y)],
        dxfattribs={"layer": "Geometry", "color": 7},
    )
    msp.add_text("FRONT VIEW", dxfattribs={"height": 2.2, "layer": "Annotations", "insert": (front_x + 5, front_y + part.height + 3)})

    # Height dimension on front view
    msp.add_line((front_x - 5, front_y), (front_x - 5, front_y + part.height), dxfattribs={"layer": "Dimensions"})
    msp.add_text(
        f"H={part.height} mm",
        dxfattribs={"height": 2.0, "layer": "Dimensions", "insert": (front_x - 18, front_y + part.height / 2.0)},
    )

    # === TITLE BLOCK BORDER ===
    border_x = front_x + 50
    border_y = front_y
    msp.add_lwpolyline(
        [(border_x, border_y), (border_x + 80, border_y), (border_x + 80, border_y + 50), (border_x, border_y + 50), (border_x, border_y)],
        dxfattribs={"layer": "TitleBlock", "color": 1},
    )
    msp.add_text("TITLE BLOCK", dxfattribs={"height": 2.5, "layer": "TitleBlock", "insert": (border_x + 3, border_y + 45)})
    msp.add_text(f"Part: {part.part_id}", dxfattribs={"height": 2.0, "layer": "TitleBlock", "insert": (border_x + 3, border_y + 40)})
    msp.add_text(f"Rev: {part.revision}", dxfattribs={"height": 2.0, "layer": "TitleBlock", "insert": (border_x + 3, border_y + 35)})
    msp.add_text("Scale: 1:1", dxfattribs={"height": 2.0, "layer": "TitleBlock", "insert": (border_x + 3, border_y + 30)})
    msp.add_text("Date: 2026-03-12", dxfattribs={"height": 2.0, "layer": "TitleBlock", "insert": (border_x + 3, border_y + 25)})
    msp.add_text(f"Material: {part.material}", dxfattribs={"height": 2.0, "layer": "TitleBlock", "insert": (border_x + 3, border_y + 20)})

    dxf_path.parent.mkdir(parents=True, exist_ok=True)
    dxf.saveas(str(dxf_path))
    return dxf_path
