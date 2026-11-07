"""Stdlib source census and deterministic-artifact consumption checks."""

import ast
import csv
import io
import math
import tokenize

import bloom
from validation import require

SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ListComp,
          ast.SetComp, ast.DictComp, ast.GeneratorExp)
DECISIONS = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp,
             ast.ExceptHandler, ast.Assert)


def decisions(node):
    if isinstance(node, DECISIONS):
        return 1
    if isinstance(node, ast.BoolOp):
        return len(node.values) - 1
    if isinstance(node, ast.comprehension):
        return 1 + len(node.ifs)
    return 0


def file_scopes(path):
    source = path.read_text(encoding="utf-8")
    comments = [token for token in tokenize.generate_tokens(io.StringIO(source).readline)
                if token.type == tokenize.COMMENT]
    require(not comments, f"inline code comments in {path.name}")
    tree = ast.parse(source)
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, SCOPES):
            score = 1 + sum(decisions(part) for part in ast.walk(node))
            rows.append({"file": path.name, "line": node.lineno, "column": node.col_offset,
                         "end_line": node.end_lineno, "end_column": node.end_col_offset,
                         "scope": getattr(node, "name", type(node).__name__),
                         "kind": type(node).__name__, "before_CC": "new", "after_CC": score})
    return rows


def census(root):
    rows = []
    for path in sorted(root.glob("*.py")):
        rows.extend(file_scopes(path))
    require(max(row["after_CC"] for row in rows) <= 10, "complexity exceeds 10")
    return rows


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def check_figure3(rows):
    require(len(rows) == 2103, "complete Figure 3 grid")
    for row in rows:
        m, k, n = (int(row[key]) for key in ("m", "k", "n"))
        require(m % k == 0 and 64 <= m <= 4096, "Figure 3 divisible dimensions")
        require(n == bloom.insertions(m, k), "Figure 3 inferred count")
        require(all(0 < float(row[key]) <= 1 for key in ("Fa", "Fs", "Fp")), "Figure 3 bounds")
        require(math.isclose(float(row["ratio"]), float(row["Fp"]) / float(row["Fs"])), "Figure 3 ratio")


def check_figure4(rows):
    require(len(rows) == 40, "complete Figure 4 collision classes")
    for row in rows:
        probability = float(row["tail_probability"])
        require(0 < probability <= 1 + 1e-14, "Figure 4 tail bounds")
        require(math.isfinite(float(row["ratio"])), "Figure 4 finite ratios")


def artifacts(directory):
    tables = read_csv(directory / "table_comparison.csv")
    require(len(tables) == 124, "all source numeric cells")
    check_figure3(read_csv(directory / "figure3.csv"))
    check_figure4(read_csv(directory / "figure4.csv"))
    require(len(read_csv(directory / "monte_carlo.csv")) == 14, "all simulation marginals")
    require(len(read_csv(directory / "dh_classes.csv")) == 10, "all SBF gcd classes")
    return {"status": "passed", "table_cells": len(tables), "figure3_points": 2103, "figure4_points": 40}
