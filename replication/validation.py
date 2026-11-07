"""Independent small-state and exact-integer checks, written before the model."""

import itertools
import math
from collections import Counter
from fractions import Fraction

import bloom


def require(condition, message):
    """Fail independently of Python's optimization flag."""
    if not condition:
        raise AssertionError(message)


def close(actual, expected, label):
    require(math.isclose(actual, expected, rel_tol=3e-12, abs_tol=2e-15), label)


def iid_worlds(m, k, n, partitioned=False):
    modulus = m // k if partitioned else m
    worlds = Counter()
    for draws in itertools.product(range(modulus), repeat=k * n):
        bits = set()
        for index, value in enumerate(draws):
            bits.add(value + (index % k) * modulus if partitioned else value)
        worlds[frozenset(bits)] += 1
    return worlds


def world_rate(worlds, query):
    hits = sum(count for bits, count in worlds.items() if set(query) <= bits)
    return Fraction(hits, sum(worlds.values()))


def tiny_iid():
    m, k, n = 4, 2, 2
    worlds = iid_worlds(m, k, n)
    conditional = bloom.conditional_rates(m, k, n)
    for d in range(1, k + 1):
        exact = world_rate(worlds, range(d))
        require(exact == bloom.conditional_exact(m, k, n, d), "tiny iid oracle")
        close(conditional[d], float(exact), "tiny iid recurrence")
    rates = [world_rate(worlds, q) for q in itertools.product(range(m), repeat=k)]
    exact_global = sum(rates) / len(rates)
    close(bloom.iid_rates(m, k, n)["Fs"], float(exact_global), "tiny iid global")
    pworlds = iid_worlds(m, k, n, True)
    close(bloom.partitioned(m, k, n), float(world_rate(pworlds, [0, 2])), "tiny PBF")
    return {"world_sequences": m ** (k * n), "global_exact": str(exact_global)}


def dh_worlds(m, k, n, partitioned):
    modulus = m // k if partitioned else m
    pairs = list(itertools.product(range(modulus), repeat=2))
    worlds = Counter()
    for inserts in itertools.product(pairs, repeat=n):
        bits = set()
        for a, b in inserts:
            bits.update(bloom.dh_positions(m, k, a, b, partitioned))
        worlds[frozenset(bits)] += 1
    return worlds


def direct_dh_histogram(m, k, query, partitioned):
    modulus = m // k if partitioned else m
    unique = list(dict.fromkeys(query))
    counts = [0] * (1 << len(unique))
    for a, b in itertools.product(range(modulus), repeat=2):
        positions = set(bloom.dh_positions(m, k, a, b, partitioned))
        mask = sum(1 << j for j, bit in enumerate(unique) if bit in positions)
        counts[mask] += 1
    return counts


def tiny_dh_layout(partitioned):
    m, k, n = 4, 2, 2
    modulus = m // k if partitioned else m
    worlds = dh_worlds(m, k, n, partitioned)
    rates = []
    for a, b in itertools.product(range(modulus), repeat=2):
        query = bloom.dh_positions(m, k, a, b, partitioned)
        hist = bloom.dh_histogram(m, k, query, partitioned)
        require(hist == direct_dh_histogram(m, k, query, partitioned), "tiny direct DH histogram")
        require(bloom.dh_exact(hist, 0) == 0, "empty DH filter")
        exact = bloom.dh_exact(hist, n)
        require(exact == world_rate(worlds, query), "tiny DH exact enumeration")
        rates.append(exact)
    return {"query_pairs": modulus ** 2, "mean_exact": str(sum(rates) / len(rates))}


def grid_case(m, k, n):
    conditional = bloom.conditional_rates(m, k, n)
    probabilities = bloom.distinct_distribution(m, k)
    close(sum(probabilities), 1.0, "query distribution normalization")
    close(sum(bloom.designated_distribution(m, k, k * n)), 1.0, "state normalization")
    for d in range(1, k + 1):
        exact = bloom.conditional_exact(m, k, n, d)
        close(conditional[d], float(exact), "reference grid integer conditional")
        require(0 <= conditional[d] <= 1, "conditional probability bounds")
        require(conditional[d] <= conditional[d - 1] + 2e-15, "conditional monotonicity")
    exact_global = bloom.standard_exact(m, k, n)
    rates = bloom.iid_rates(m, k, n)
    close(rates["Fs"], float(exact_global), "reference grid integer global")
    require(rates["Fa"] <= rates["Fs"] + 2e-15, "Jensen lower bound")


def check_empty():
    for m, k in [(4, 2), (64, 4), (512, 16)]:
        values = bloom.iid_rates(m, k, 0)
        require(all(value == 0 for value in values.values()), "empty-filter rates")
        grid_case(m, k, 0)
    return 3


def histogram_valid(hist, total):
    require(sum(hist) == total, "DH histogram normalization")
    require(all(isinstance(c, int) and c >= 0 for c in hist), "DH integer counts")
    avoid = bloom.avoidance_counts(hist)
    for subset, count in enumerate(avoid):
        direct = sum(c for mask, c in enumerate(hist) if mask & subset == 0)
        require(count == direct, "subset zeta avoidance")


def dh_symmetry(m, k):
    mod = m // k
    for gcd in bloom.step_classes(m):
        step = gcd % m
        original = bloom.dh_positions(m, k, 0, step)
        transformed = bloom.dh_positions(m, k, 17, 3 * step % m)
        first = bloom.dh_histogram(m, k, original)
        second = bloom.dh_histogram(m, k, transformed)
        require(first == second, "SBF translation and odd-unit symmetry")
        histogram_valid(first, m * m)
    base = bloom.dh_histogram(m, k, bloom.dh_positions(m, k, 0, 0, True), True)
    for a, b in [(1, 0), (17, 3), (mod - 1, mod - 1), (4, mod // 2)]:
        other = bloom.dh_histogram(m, k, bloom.dh_positions(m, k, a, b, True), True)
        require(base == other, "PBF pair subtraction symmetry")
    histogram_valid(base, mod * mod)


def dh_one_bit(m, k, n):
    total_distinct = sum(len(set(bloom.dh_positions(m, k, 0, b))) for b in range(m))
    one_insert_hit = Fraction(total_distinct, m * m)
    expected = 1 - (1 - one_insert_hit) ** n
    actual = bloom.dh_exact(bloom.dh_histogram(m, k, [0]), n)
    require(actual == expected, "DH exact one-bit marginal")
    return {"one_insert_hit_exact": str(one_insert_hit), "fpr_exact": str(actual)}


def run(grid):
    tiny = {"iid": tiny_iid(), "SBF_DH": tiny_dh_layout(False), "PBF_DH": tiny_dh_layout(True)}
    for m, k, n in sorted(set(grid)):
        grid_case(m, k, n)
    empty = check_empty()
    dh_symmetry(512, 8)
    one_bit = dh_one_bit(512, 8, bloom.insertions(512, 8))
    return {"status": "passed", "tiny": tiny, "grid_cases": len(set(grid)),
            "empty_cases": empty, "DH_one_bit": one_bit}
