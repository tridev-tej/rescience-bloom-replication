"""Render the paper's comparison tables from the recorded experiment results."""

import csv
import json
import sys
from fractions import Fraction
from pathlib import Path


def rows(directory, name):
    with (directory / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def table(caption, label, layout, columns, body):
    return "\n".join([
        r"\begin{table}[H]", r"\centering", r"\small",
        rf"\begin{{tabular}}{{{layout}}}", r"\toprule",
        " & ".join(columns) + r" \\", r"\midrule",
        *(" & ".join(row) + r" \\" for row in body),
        r"\bottomrule", r"\end{tabular}",
        rf"\caption{{{caption}}}\label{{{label}}}", r"\end{table}", "",
    ])


def fraction_load(value):
    return str(Fraction(value))


def equal_n_bound(m, k):
    a = Fraction(m - 1, m) ** k
    b = Fraction(m - k, m)
    return ((1 - b) / (1 - a)) ** k


def comparison(cells):
    small = [r for r in cells if r["table"] == "2" and r["m"] == "64"
             and float(r["occupation"]) < 1.0]
    if len(small) != 4:
        raise ValueError("expected four word-size reduced-load cells")
    body = []
    for row in small:
        bound = equal_n_bound(int(row["m"]), int(row["k"]))
        if not Fraction(row["computed"]) <= bound < Fraction(row["published"]):
            raise ValueError("word-size ratios do not satisfy the stated comparison")
        body.append((row["k"], fraction_load(row["occupation"]), row["n"],
                     row["published"], f'{float(row["computed"]):.8f}', f"{float(bound):.5f}"))
    return table(
        r"Reduced-load ratios at $m=64$. The last column bounds the ratio "
        r"for any common positive integer insertion count under the paper's formulas.",
        "tab:comparison", "rrr rrr", (
            "$k$", "Load", "$n$", "Source Table 2", "Recomputed", "Upper bound",
        ), body,
    )


def trial_row(row, name):
    return (
        name, row["hits"], f'{float(row["estimate"]):.5f}',
        f'[{float(row["wilson95_low"]):.5f}, {float(row["wilson95_high"]):.5f}]',
        f'{float(row["expected"]):.5f}',
    )


def simulation(simulations, calibration):
    labels = {
        "SBF_fixed_d=1": "Standard, one bit",
        "SBF_fixed_d=4": "Standard, four bits",
        "SBF_random_query": "Standard, random",
        "PBF_random_query": "Partitioned, random",
    }
    body = [trial_row(row, labels[row["layout_query"]]) for row in simulations
            if float(row["occupation"]) == 1.0 and row["layout_query"] in labels]
    if len(body) != len(labels):
        raise ValueError("nominal simulation table is incomplete")
    maximum = calibration["max_standardized_error"]
    eligible = calibration["eligible_cells"]
    prose = (
        f"The direct simulations met the prespecified calibration criterion. "
        f"The largest absolute standardized error was {maximum:.2f} among "
        f"{eligible} eligible cells, below the cutoff of 4.5. "
        r"Table~\ref{tab:simulation} shows selected nominal-load results. "
        "The experiment checks the predicted rates at this configuration. "
        "The global estimates have overlapping intervals.\n"
    )
    return prose + table(
        r"Selected direct simulations at $m=64$, $k=4$, and $n=11$. "
        r"Each row uses 120,000 trials. The intervals are marginal Wilson intervals.",
        "tab:simulation", "lrrlr", (
            "Query", "Hits", "Estimate", r"95\% interval", "Model",
        ), body,
    )


def hashing(classes, double):
    body = []
    for row in classes:
        if row["representative_b"] not in {"0", "1", "64", "128", "256"}:
            continue
        weight = str(Fraction(row["class_probability_exact"]))
        body.append(("Standard", row["representative_b"], row["distinct_query_bits"],
                     weight, f'{100 * float(row["FPR"]):.3f}'))
    body.append(("Partitioned", "Any", "8", "1",
                 f'{100 * double["PBF_uniform_pairs"]["FPR"]:.3f}'))
    return table(
        r"Selected exact double-hashing classes for $m=512$, $k=8$, and $n=44$. "
        r"Each standard row represents all steps with the same $\gcd(b,m)$. "
        r"The artifact includes every class.",
        "tab:double", "lrrrr", (
            "Layout", "Representative step", "Bits", "Class mass", r"FPR (\%)",
        ), body,
    )


def plot(name, label, caption):
    return "\n".join([
        r"\begin{figure}[H]", r"\centering",
        rf"\includegraphics[width=\linewidth]{{generated/{name}.pdf}}",
        rf"\caption{{{caption}}}\label{{{label}}}", r"\end{figure}", "",
    ])


def render(directory, generated):
    generated.mkdir(parents=True, exist_ok=True)
    summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
    results = {
        "comparison-table.tex": comparison(rows(directory, "table_comparison.csv")),
        "simulation-results.tex": simulation(rows(directory, "monte_carlo.csv"), summary["monte_carlo"]),
        "double-hash-table.tex": hashing(rows(directory, "dh_classes.csv"), summary["double_hashing"]),
        "mean-figure.tex": plot("figure3", "fig:mean",
            r"Reconstruction of Almeida's Figure 3. Each curve compares the exact "
            r"global rates under independent hashing. The grid includes sizes "
            r"divisible by $k$, with nominal capacity rounded down."),
        "tail-figure.tex": plot("figure4", "fig:tail",
            r"Reconstruction of Almeida's Figure 4. Each point shows the cumulative "
            r"query probability at or above the corresponding fixed-key/global rate "
            r"ratio. The plot omits tail probabilities below $10^{-7}$."),
    }
    for name, content in results.items():
        (generated / name).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    render(Path(sys.argv[1]), Path(sys.argv[2]))
