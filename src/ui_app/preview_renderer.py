from __future__ import annotations

from pathlib import Path


def _ensure_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _vertex_xyz(vertex) -> tuple[float, float, float]:
    if hasattr(vertex, "x") and hasattr(vertex, "y") and hasattr(vertex, "z"):
        return float(vertex.x), float(vertex.y), float(vertex.z)
    if hasattr(vertex, "toTuple"):
        x, y, z = vertex.toTuple()
        return float(x), float(y), float(z)
    x, y, z = vertex
    return float(x), float(y), float(z)


def _set_axes_equal(ax, points: list[tuple[float, float, float]]) -> None:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]

    x_mid = (max(xs) + min(xs)) / 2.0
    y_mid = (max(ys) + min(ys)) / 2.0
    z_mid = (max(zs) + min(zs)) / 2.0
    max_range = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0) / 2.0

    ax.set_xlim(x_mid - max_range, x_mid + max_range)
    ax.set_ylim(y_mid - max_range, y_mid + max_range)
    ax.set_zlim(z_mid - max_range, z_mid + max_range)



def render_step_preview(step_path: Path, output_path: Path, title: str | None = None) -> Path:
    import cadquery as cq
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    plt = _ensure_matplotlib()

    workplane = cq.importers.importStep(str(step_path))
    shape = workplane.val()
    vertices, triangles = shape.tessellate(0.8)

    points = [_vertex_xyz(vertex) for vertex in vertices]
    mesh = [[points[index] for index in triangle] for triangle in triangles]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(8, 6), dpi=140)
    ax = fig.add_subplot(111, projection="3d")
    poly = Poly3DCollection(mesh, facecolor="#8fb8de", edgecolor="#3d5a80", linewidths=0.15, alpha=0.95)
    ax.add_collection3d(poly)
    _set_axes_equal(ax, points)
    ax.view_init(elev=24, azim=36)
    ax.set_facecolor("#f7f8fb")
    fig.patch.set_facecolor("white")
    ax.set_axis_off()
    ax.set_title(title or step_path.stem, fontsize=12, color="#223046", pad=12)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path



def render_dxf_preview(dxf_path: Path, output_path: Path, title: str | None = None) -> Path:
    import ezdxf
    from matplotlib.patches import Circle

    plt = _ensure_matplotlib()

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6), dpi=140)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#fcfcfd")

    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    def update_bounds(x: float, y: float) -> None:
        nonlocal min_x, min_y, max_x, max_y
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    for entity in msp:
        entity_type = entity.dxftype()

        if entity_type == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            ax.plot([start.x, end.x], [start.y, end.y], color="#264653", linewidth=1.0)
            update_bounds(start.x, start.y)
            update_bounds(end.x, end.y)

        elif entity_type == "LWPOLYLINE":
            points = [(point[0], point[1]) for point in entity.get_points()]
            if entity.closed and points:
                points.append(points[0])
            if points:
                xs = [point[0] for point in points]
                ys = [point[1] for point in points]
                ax.plot(xs, ys, color="#1d3557", linewidth=1.0)
                for x, y in points:
                    update_bounds(x, y)

        elif entity_type == "CIRCLE":
            center = entity.dxf.center
            radius = float(entity.dxf.radius)
            ax.add_patch(Circle((center.x, center.y), radius, fill=False, color="#2a9d8f", linewidth=1.0))
            update_bounds(center.x - radius, center.y - radius)
            update_bounds(center.x + radius, center.y + radius)

        elif entity_type in {"TEXT", "MTEXT"}:
            insert = entity.dxf.insert
            text = entity.plain_text() if entity_type == "MTEXT" else entity.dxf.text
            ax.text(insert.x, insert.y, text[:36], fontsize=5.5, color="#6d597a")
            update_bounds(insert.x, insert.y)

    if min_x == float("inf"):
        min_x, min_y, max_x, max_y = 0.0, 0.0, 100.0, 100.0

    pad_x = max((max_x - min_x) * 0.08, 10.0)
    pad_y = max((max_y - min_y) * 0.08, 10.0)
    ax.set_xlim(min_x - pad_x, max_x + pad_x)
    ax.set_ylim(min_y - pad_y, max_y + pad_y)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title(title or dxf_path.stem, fontsize=12, color="#223046", pad=10)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path
