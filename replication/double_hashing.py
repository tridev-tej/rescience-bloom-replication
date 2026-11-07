"""Exact double-hashing extension and concrete Section 5 witnesses."""

import math
from fractions import Fraction

import bloom
from validation import require


def fraction_columns(value):
    return {"FPR": float(value), "numerator": str(value.numerator), "denominator": str(value.denominator)}


def standard_sweep(m, k, n):
    rows = []
    mean = Fraction(0)
    for gcd in bloom.step_classes(m):
        step_count = sum(math.gcd(b, m) == gcd for b in range(m))
        mass = Fraction(step_count, m)
        query = bloom.dh_positions(m, k, 0, gcd % m)
        histogram = bloom.dh_histogram(m, k, query)
        value = bloom.dh_exact(histogram, n)
        mean += mass * value
        rows.append({"m": m, "k": k, "n": n, "gcd": gcd, "representative_b": gcd % m,
                     "period": m // gcd, "distinct_query_bits": len(set(query)),
                     "step_count": step_count, "query_pair_count": m * step_count,
                     "class_probability": float(mass), "class_probability_exact": str(mass),
                     "insert_pairs": sum(histogram), "weighted_FPR": float(mass * value),
                     **fraction_columns(value)})
    require(sum(row["query_pair_count"] for row in rows) == m * m, "all gcd classes covered")
    return rows, mean


def run():
    m, k = 512, 8
    n = bloom.insertions(m, k)
    rows, standard = standard_sweep(m, k, n)
    query = bloom.dh_positions(m, k, 0, 0, True)
    histogram = bloom.dh_histogram(m, k, query, True)
    partitioned = bloom.dh_exact(histogram, n)
    summary = {"scope": "extension, not a published table", "m": m, "k": k, "n": n,
               "SBF_uniform_pairs": fraction_columns(standard),
               "PBF_uniform_pairs": fraction_columns(partitioned),
               "PBF_query_pair_count": (m // k) ** 2,
               "iid": bloom.iid_rates(m, k, n)}
    avoidance = bloom.avoidance_counts(histogram)
    counts = [{"subset": subset, "subset_size": subset.bit_count(), "avoid_count": count,
               "insert_pairs": sum(histogram)} for subset, count in enumerate(avoidance)]
    return rows, summary, counts


def witness(scenario, partitioned, a, b, other=None):
    m, k = 512, 8
    positions = bloom.dh_positions(m, k, a, b, partitioned)
    second = () if other is None else bloom.dh_positions(m, k, *other, partitioned)
    return {"scenario": scenario, "layout": "PBF" if partitioned else "SBF",
            "m": m, "k": k, "modulus": m // k if partitioned else m,
            "a": a, "b": b, "positions": ";".join(map(str, positions)),
            "distinct_physical_bits": len(set(positions)),
            "other_a": "" if other is None else other[0],
            "other_b": "" if other is None else other[1],
            "other_positions": ";".join(map(str, second)),
            "overlap_physical_bits": "" if other is None else len(set(positions) & set(second))}


def witnesses():
    rows = []
    for partitioned in (False, True):
        modulus = 64 if partitioned else 512
        for divisor in (1, 2, 4):
            b = 0 if divisor == 1 else modulus // divisor
            row = witness(f"repetition_1/{divisor}", partitioned, 7, b)
            require(row["distinct_physical_bits"] == (8 if partitioned else divisor), "repetition witness")
            rows.append(row)
        reverse = witness("reversal", partitioned, 7, 5, (42, modulus - 5))
        shift = witness("shift", partitioned, 7, 5, (12, 5))
        require(reverse["overlap_physical_bits"] == (0 if partitioned else 8), "reversal witness")
        require(shift["overlap_physical_bits"] == (0 if partitioned else 7), "shift witness")
        rows.extend([reverse, shift])
    return rows
