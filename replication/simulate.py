"""Direct seeded iid filter insertions; no sampling from analytical FPRs."""

import math
import random

import bloom

SEED = 20261107
TRIALS = 120000
Z95 = 1.959963984540054
CALIBRATION_LIMIT = 4.5


def wilson(hits, trials):
    rate = hits / trials
    scale = 1 + Z95 ** 2 / trials
    center = (rate + Z95 ** 2 / (2 * trials)) / scale
    half = Z95 * math.sqrt(rate * (1 - rate) / trials + Z95 ** 2 / (4 * trials ** 2)) / scale
    return center - half, center + half


def result(label, occupation, n, seed, hits, expected):
    low, high = wilson(hits, TRIALS)
    eligible = min(TRIALS * expected, TRIALS * (1 - expected)) >= 20
    error = (hits - TRIALS * expected) / math.sqrt(TRIALS * expected * (1 - expected))
    return {"layout_query": label, "m": 64, "k": 4, "occupation": occupation,
            "n": n, "seed": seed, "hits": hits, "trials": TRIALS,
            "estimate": hits / TRIALS, "expected": expected,
            "wilson95_low": low, "wilson95_high": high,
            "standardized_error": error, "calibration_eligible": eligible,
            "within_4_5": abs(error) <= CALIBRATION_LIMIT if eligible else "not_required"}


def standard_worlds(n, seed, random_query):
    rng = random.Random(seed)
    hits = [0] * 4
    global_hits = 0
    for _ in range(TRIALS):
        bits = 0
        for _ in range(4 * n):
            bits |= 1 << rng.randrange(64)
        for d in range(1, 5):
            mask = (1 << d) - 1
            hits[d - 1] += (bits & mask) == mask
        if random_query:
            query = sum_query_mask(rng)
            global_hits += (bits & query) == query
    return hits, global_hits


def sum_query_mask(rng):
    query = 0
    for _ in range(4):
        query |= 1 << rng.randrange(64)
    return query


def partitioned_worlds(n):
    rng = random.Random(SEED + 3)
    hits = 0
    for _ in range(TRIALS):
        bits = [0] * 4
        for _ in range(n):
            for part in range(4):
                bits[part] |= 1 << rng.randrange(16)
        query = [rng.randrange(16) for _ in range(4)]
        hits += all(bits[part] & (1 << query[part]) for part in range(4))
    return hits


def run():
    rows = []
    for index, occupation in enumerate((0.25, 0.5, 1.0)):
        n = bloom.insertions(64, 4, occupation)
        hits, global_hits = standard_worlds(n, SEED + index, occupation == 1.0)
        conditional = bloom.conditional_rates(64, 4, n)
        for d, count in enumerate(hits, start=1):
            rows.append(result(f"SBF_fixed_d={d}", occupation, n, SEED + index, count, conditional[d]))
        if occupation == 1.0:
            rows.append(result("SBF_random_query", occupation, n, SEED + index,
                               global_hits, bloom.iid_rates(64, 4, n)["Fs"]))
    n = bloom.insertions(64, 4)
    rows.append(result("PBF_random_query", 1.0, n, SEED + 3,
                       partitioned_worlds(n), bloom.partitioned(64, 4, n)))
    maximum = max(abs(row["standardized_error"]) for row in rows if row["calibration_eligible"])
    return rows, {"criterion": "max eligible absolute standardized error <= 4.5",
                  "max_standardized_error": maximum,
                  "status": "passed" if maximum <= CALIBRATION_LIMIT else "failed",
                  "eligible_cells": sum(row["calibration_eligible"] for row in rows)}
