"""Published-cell comparisons and predeclared integer-rounding diagnostics."""

import math

import bloom
import published


def cell(table, m, k, occupation, metric, printed, computed):
    decimals = len(printed.split(".")[1])
    tolerance = 0.5 * 10 ** (-decimals) + 1e-12
    difference = computed - float(printed)
    return {"table": table, "m": m, "k": k, "occupation": occupation,
            "n": bloom.insertions(m, k, occupation), "metric": metric,
            "published": printed, "computed": computed, "difference": difference,
            "tolerance": tolerance, "matches": abs(difference) <= tolerance}


def ratio(m, k, n):
    rates = bloom.iid_rates(m, k, n)
    return rates["Fp"] / rates["Fs"]


def table1():
    rows = []
    for m, k, *printed in published.TABLE1:
        n = bloom.insertions(m, k)
        rates = bloom.iid_rates(m, k, n)
        rates["Fp/Fs"] = rates["Fp"] / rates["Fs"]
        for metric, source in zip(("Fa", "Fs", "Fp", "Fp/Fs"), printed):
            rows.append(cell(1, m, k, 1.0, metric, source, rates[metric]))
    return rows


def table2():
    rows = []
    for m, k, *printed in published.TABLE2:
        for occupation, source in zip(published.OCCUPATIONS, printed):
            value = ratio(m, k, bloom.insertions(m, k, occupation))
            rows.append(cell(2, m, k, occupation, "Fp/Fs", source, value))
    return rows


def table3():
    rows = []
    for occupation, m, k, *printed in published.TABLE3:
        n = bloom.insertions(m, k, occupation)
        conditional = bloom.conditional_rates(m, k, n)
        standard = bloom.iid_rates(m, k, n)["Fs"]
        for collisions, source in enumerate(printed):
            value = conditional[k - collisions] / standard
            rows.append(cell(3, m, k, occupation, f"c={collisions}", source, value))
    return rows


def table4():
    rows = []
    for m, k, *printed in published.TABLE4:
        probabilities = bloom.distinct_distribution(m, k)
        values = [math.fsum(probabilities[:k])] + [probabilities[k - c] for c in range(4)]
        for metric, source, value in zip(("some", "c=0", "c=1", "c=2", "c=3"), printed, values):
            row = cell(4, m, k, 1.0, metric, source, value)
            row["occupation"] = ""
            row["n"] = ""
            rows.append(row)
    return rows


def approximate_implied_n(m, k, rate):
    return math.log1p(-(rate ** (1 / k))) / (k * math.log1p(-1 / m))


def insertion_diagnostics():
    rows = []
    for m, k, printed, *_ in published.TABLE1:
        value = float(printed)
        lower = approximate_implied_n(m, k, value - 5e-9)
        upper = approximate_implied_n(m, k, value + 5e-9)
        candidates = list(range(math.ceil(lower), math.floor(upper) + 1))
        rows.append({"m": m, "k": k, "printed_Fa": printed,
                     "primary_floor_n": bloom.insertions(m, k),
                     "implied_n": approximate_implied_n(m, k, value),
                     "implied_n_lower": lower, "implied_n_upper": upper,
                     "consistent_integer_n": ";".join(map(str, candidates))})
    return rows


def alternative_value(row, n):
    m, k, metric = row["m"], row["k"], row["metric"]
    rates = bloom.iid_rates(m, k, n)
    if metric == "Fp/Fs":
        return rates["Fp"] / rates["Fs"]
    if metric.startswith("c="):
        d = k - int(metric[2:])
        return bloom.conditional_rates(m, k, n)[d] / rates["Fs"]
    return rates[metric]


def rounding_diagnostics(rows):
    diagnostics = []
    for row in rows:
        if row["matches"] or row["table"] == 4:
            continue
        target = row["occupation"] * row["m"] * math.log(2) / row["k"]
        for convention, n in [("floor", math.floor(target)), ("nearest", round(target)), ("ceil", math.ceil(target))]:
            value = alternative_value(row, n)
            diagnostics.append({"table": row["table"], "m": row["m"], "k": row["k"],
                                "occupation": row["occupation"], "metric": row["metric"],
                                "published": row["published"], "convention": convention,
                                "n": n, "computed": value,
                                "matches": abs(value - float(row["published"])) <= row["tolerance"]})
    return diagnostics


def figure3():
    rows = []
    for k in (4, 8, 12, 16):
        first = ((64 + k - 1) // k) * k
        for m in range(first, 4097, k):
            n = bloom.insertions(m, k)
            rates = bloom.iid_rates(m, k, n)
            rows.append({"m": m, "k": k, "n": n, **rates, "ratio": rates["Fp"] / rates["Fs"]})
    return rows


def figure4():
    rows = []
    for m, k in published.FIGURE4:
        n = bloom.insertions(m, k)
        standard = bloom.iid_rates(m, k, n)["Fs"]
        conditional = bloom.conditional_rates(m, k, n)
        probabilities = bloom.distinct_distribution(m, k)
        for d in range(k, 0, -1):
            rows.append({"m": m, "k": k, "n": n, "d": d, "collisions": k - d,
                         "class_probability": probabilities[d],
                         "tail_probability": math.fsum(probabilities[1:d + 1]),
                         "conditional_FPR": conditional[d], "global_FPR": standard,
                         "ratio": conditional[d] / standard})
    return rows
