"""Run the scientific replication from its project root."""

import sys
import datetime
import platform
import time
from pathlib import Path

import bloom
import double_hashing
import output
import quality
import simulate
import tables
import validation


def write_tables(directory):
    rows = tables.table1() + tables.table2() + tables.table3() + tables.table4()
    output.write_csv(directory / "table_comparison.csv", rows)
    output.write_csv(directory / "discrepancies.csv", [row for row in rows if not row["matches"]])
    output.write_csv(directory / "insertion_diagnostics.csv", tables.insertion_diagnostics())
    diagnostics = tables.rounding_diagnostics(rows)
    output.write_csv(directory / "rounding_diagnostics.csv", diagnostics)
    output.table_tex(directory / "tables_1_4.tex", rows)
    return rows, diagnostics


def write_figures(directory):
    figure3 = tables.figure3()
    figure4 = tables.figure4()
    output.write_csv(directory / "figure3.csv", figure3)
    output.write_csv(directory / "figure4.csv", figure4)
    output.figure_svg(directory / "figure3.svg", figure3)
    output.figure_svg(directory / "figure4.svg", figure4, True)
    landmarks = [row for row in figure4 if (row["m"], row["k"]) == (512, 16)
                 and row["collisions"] in (3, 5)]
    output.write_json(directory / "figure4_landmarks.json", landmarks)
    return figure3, figure4


def dh_count_rows():
    rows = []
    for gcd in bloom.step_classes(512):
        query = bloom.dh_positions(512, 8, 0, gcd % 512)
        rows.extend(projected_count_rows("SBF", gcd, query, False))
    query = bloom.dh_positions(512, 8, 0, 0, True)
    rows.extend(projected_count_rows("PBF", "all", query, True))
    return rows


def projected_count_rows(layout, gcd, query, partitioned):
    histogram = bloom.dh_histogram(512, 8, query, partitioned)
    avoidance = bloom.avoidance_counts(histogram)
    return [{"layout": layout, "gcd_class": gcd, "subset": subset,
             "subset_size": subset.bit_count(), "exact_hit_mask_count": count,
             "avoid_subset_count": avoidance[subset], "total_insert_pairs": sum(histogram)}
            for subset, count in enumerate(histogram)]


def write_dh(directory):
    classes, summary, _ = double_hashing.run()
    output.write_csv(directory / "dh_classes.csv", classes)
    output.write_json(directory / "dh_summary.json", summary)
    output.write_csv(directory / "dh_projected_counts.csv", dh_count_rows())
    output.write_csv(directory / "dh_witnesses.csv", double_hashing.witnesses())
    return summary


def comparison_summary(rows):
    return {str(table): {"cells": sum(row["table"] == table for row in rows),
                         "exceptions": sum(row["table"] == table and not row["matches"] for row in rows)}
            for table in range(1, 5)}


def report_lines(summary):
    comparisons = summary["published_comparison"]
    exceptions = sum(group["exceptions"] for group in comparisons.values())
    dh = summary["double_hashing"]
    calibration = summary["monte_carlo"]
    return ["Invariant and exact small-state validation: passed",
            f"Published cells: 124; matched: {124 - exceptions}; exceptions: {exceptions}",
            "Table exceptions: " + ", ".join(f"T{key}={value['exceptions']}" for key, value in comparisons.items()),
            "Figure CSV points: Figure 3=2103; Figure 4=40",
            f"Monte Carlo: {calibration['status']}; 14 marginals; 120000 trials each; max |z|={calibration['max_standardized_error']:.9f}",
            f"DH SBF mean FPR: {dh['SBF_uniform_pairs']['FPR']:.15g}",
            f"DH PBF mean FPR: {dh['PBF_uniform_pairs']['FPR']:.15g}",
            f"Complexity: {summary['complexity_scopes']} scopes; maximum CC={summary['maximum_CC']}",
            "Protocol deviations: none; integer capacity convention remains inferred",
            "Results: results/; measurements: measurements/"]


def record_measurements(root, elapsed):
    gst = datetime.timezone(datetime.timedelta(hours=4))
    measurements = {"elapsed_seconds": elapsed, "python": sys.version,
                    "platform": platform.platform(),
                    "recorded_at_GST": datetime.datetime.now(gst).isoformat(),
                    "command": "python3 replicate.py"}
    output.write_json(root / "measurements/run.json", measurements)


def run(root):
    directory = root / "results"
    directory.mkdir(exist_ok=True)
    (root / "measurements").mkdir(exist_ok=True)
    scopes = quality.census(root)
    output.write_csv(directory / "complexity.csv", scopes)
    rows, diagnostics = write_tables(directory)
    grid = [(row["m"], row["k"], row["n"]) for row in rows if row["table"] != 4]
    checked = validation.run(grid)
    write_figures(directory)
    dh = write_dh(directory)
    samples, calibration = simulate.run()
    output.write_csv(directory / "monte_carlo.csv", samples)
    artifacts = quality.artifacts(directory)
    summary = {"published_comparison": comparison_summary(rows), "validation": checked,
               "artifacts": artifacts, "double_hashing": dh, "monte_carlo": calibration,
               "rounding_diagnostic_matching_rows": sum(row["matches"] for row in diagnostics),
               "complexity_scopes": len(scopes), "maximum_CC": max(row["after_CC"] for row in scopes),
               "protocol_deviations": [], "capacity_convention": "inferred floor"}
    output.write_json(directory / "summary.json", summary)
    output.write_json(directory / "provenance.json", output.source_hashes(root))
    text = "\n".join(report_lines(summary)) + "\n"
    (directory / "run_summary.txt").write_text(text, encoding="utf-8")
    output.write_json(directory / "sha256.json", output.manifest(directory))
    print(text, end="", flush=True)
    validation.require(calibration["status"] == "passed", "Monte Carlo calibration failed; outputs retained")


def main():
    root = Path(__file__).resolve().parent
    validation.require(sys.version_info >= (3, 11), "Python 3.11+ required")
    validation.require(Path.cwd() == root, "run python3 replicate.py from the project root")
    started = time.perf_counter()
    run(root)
    record_measurements(root, time.perf_counter() - started)


if __name__ == "__main__":
    main()
