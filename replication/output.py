"""Stable CSV, JSON, LaTeX and standalone SVG artifacts."""

import csv
import hashlib
import html
import json
import math


def scalar(value):
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, bool):
        return str(value).lower()
    return value


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: scalar(value) for key, value in row.items()} for row in rows)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_tex(path, rows):
    lines = [r"% Generated from actual execution; requires longtable."]
    for table in range(1, 5):
        lines.extend([r"\begin{longtable}{rrrllrr}",
                      f"\\caption{{Table {table}: recomputed and published values.}}\\\\",
                      r"$m$ & $k$ & $n$ & Load & Metric & Recomputed & Published \\", r"\hline"])
        for row in rows:
            if row["table"] == table:
                values = [row["m"], row["k"], row["n"], row["occupation"],
                          row["metric"], format(row["computed"], ".10g"), row["published"]]
                lines.append(" & ".join(map(str, values)) + r" \\")
        lines.extend([r"\end{longtable}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def coordinates(x, y, bounds, logarithmic):
    xmin, xmax, ymin, ymax = bounds
    if logarithmic:
        x, xmin, xmax = math.log10(x), math.log10(xmin), math.log10(xmax)
        y, ymin, ymax = math.log10(y), math.log10(ymin), math.log10(ymax)
    return 90 + 750 * (x - xmin) / (xmax - xmin), 450 - 380 * (y - ymin) / (ymax - ymin)


def svg_axes(title, xlabel, ylabel, bounds, logarithmic):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">',
             '<rect width="960" height="540" fill="white"/>',
             '<g font-family="serif" font-size="21" fill="#111">',
             f'<text x="480" y="30" text-anchor="middle">{html.escape(title)}</text>',
             '<path d="M90 65V450H845" fill="none" stroke="#111"/>',
             f'<text x="465" y="510" text-anchor="middle">{html.escape(xlabel)}</text>',
             f'<text transform="translate(24 260) rotate(-90)" text-anchor="middle">{html.escape(ylabel)}</text>']
    xmin, xmax, ymin, ymax = bounds
    xticks = [10 ** exponent for exponent in range(-7, 1)] if logarithmic else [64, 512, 1024, 2048, 4096]
    yticks = [1, 10, 100] if logarithmic else [index / 4 for index in range(4, int(ymax * 4) + 1)]
    for x in xticks:
        px, _ = coordinates(x, ymin, bounds, logarithmic)
        parts.append(f'<path d="M{px:.3f} 450v6" stroke="#111"/><text x="{px:.3f}" y="478" text-anchor="middle">{x:g}</text>')
    for y in yticks:
        _, py = coordinates(xmin, y, bounds, logarithmic)
        parts.append(f'<path d="M84 {py:.3f}H840" stroke="#ddd"/><text x="77" y="{py + 5:.3f}" text-anchor="end">{y:g}</text>')
    return parts


def svg_series(parts, groups, bounds, logarithmic):
    colors = ["#185b91", "#b34827", "#267d47", "#823f91", "#555555"]
    for index, (label, points) in enumerate(groups.items()):
        drawn = staircase(points) if logarithmic else points
        pixels = [coordinates(x, y, bounds, logarithmic) for x, y in drawn]
        data = " ".join(f"{x:.3f},{y:.3f}" for x, y in pixels)
        color = colors[index]
        parts.append(f'<polyline points="{data}" fill="none" stroke="{color}" stroke-width="2.2"/>')
        position = 83 + 24 * index
        parts.append(f'<path d="M650 {position}h25" stroke="{color}" stroke-width="2"/><text x="685" y="{position + 5}">{html.escape(label)}</text>')


def staircase(points):
    drawn = [points[0]]
    for x, y in points[1:]:
        drawn.extend([(x, drawn[-1][1]), (x, y)])
    return drawn


def figure_groups(rows, tail):
    groups = {}
    for row in rows:
        label = f'm={row["m"]}, k={row["k"]}' if tail else f'k={row["k"]}'
        x = row["tail_probability"] if tail else row["m"]
        if tail and x < 1e-7:
            continue
        groups.setdefault(label, []).append((x, row["ratio"]))
    return groups


def figure_svg(path, rows, tail=False):
    groups = figure_groups(rows, tail)
    bounds = (1e-7, 1, 0.5, 150) if tail else (64, 4096, 1, math.ceil(max(r["ratio"] for r in rows) * 10) / 10)
    title = "Figure 4 reconstruction: inverse upper tail (display cutoff 1e-7)" if tail else "Figure 3 reconstruction: inferred integer nominal load"
    xlabel = "Upper-tail probability" if tail else "Filter size m (bits)"
    ylabel = "Per-element / global FPR" if tail else "Partitioned / standard FPR"
    parts = svg_axes(title, xlabel, ylabel, bounds, tail)
    svg_series(parts, groups, bounds, tail)
    parts.append("</g></svg>\n")
    path.write_text("\n".join(parts), encoding="utf-8")


def manifest(directory):
    return {path.name: digest(path) for path in sorted(directory.iterdir()) if path.name != "sha256.json"}


def source_hashes(root):
    paths = [root.parent / "PROTOCOL.md", root.parent / "SOURCE.md",
             root / "VALIDATION_PLAN.md"]
    paths.extend(sorted(root.glob("*.py")))
    return {str(path.relative_to(root.parent)): digest(path) for path in paths}
