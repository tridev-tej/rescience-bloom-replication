"""Finite Bloom-filter probabilities with independent integer oracles."""

import math
from fractions import Fraction
from functools import lru_cache


def check_parameters(m, k, n):
    if not (isinstance(m, int) and isinstance(k, int) and isinstance(n, int)):
        raise ValueError("m, k, n must be integers")
    if not (m >= k >= 1 and n >= 0 and m % k == 0):
        raise ValueError("require m >= k >= 1, k divides m, n >= 0")


def insertions(m, k, occupation=1.0):
    return math.floor(occupation * m * math.log(2) / k)


def designated_distribution(m, d, draws):
    """Track occupied positions among d designated physical bits."""
    state = [1.0] + [0.0] * d
    for draw in range(draws):
        for j in range(min(d, draw + 1), 0, -1):
            state[j] = (state[j] * (m - d + j) + state[j - 1] * (d - j + 1)) / m
        state[0] *= (m - d) / m
    return state


@lru_cache(maxsize=None)
def conditional_rates(m, k, n):
    """Recover every d-bit rate from factorial moments of one k-bit chain."""
    check_parameters(m, k, n)
    state = designated_distribution(m, k, k * n)
    rates = [1.0]
    for d in range(1, k + 1):
        terms = (state[j] * math.comb(j, d) / math.comb(k, d) for j in range(d, k + 1))
        rates.append(math.fsum(terms))
    return tuple(rates)


def distinct_counts(m, k):
    """Integer counts of ordered k draws yielding each number of distinct bits."""
    counts = [1] + [0] * k
    for draw in range(k):
        for d in range(draw + 1, 0, -1):
            counts[d] = d * counts[d] + (m - d + 1) * counts[d - 1]
        counts[0] = 0
    return counts


def distinct_distribution(m, k):
    return tuple(count / m ** k for count in distinct_counts(m, k))


def bit_set_probability(modulus, draws):
    if modulus == 1:
        return float(draws > 0)
    return -math.expm1(draws * math.log1p(-1 / modulus))


def partitioned(m, k, n):
    check_parameters(m, k, n)
    return bit_set_probability(m // k, n) ** k


def iid_rates(m, k, n):
    conditional = conditional_rates(m, k, n)
    probabilities = distinct_distribution(m, k)
    standard = math.fsum(p * c for p, c in zip(probabilities, conditional))
    return {"Fa": bit_set_probability(m, k * n) ** k,
            "Fs": standard, "Fp": partitioned(m, k, n)}


def conditional_numerator(m, draws, d):
    """Exact inclusion-exclusion count for d fixed bits all occupied."""
    return sum((-1) ** j * math.comb(d, j) * (m - j) ** draws for j in range(d + 1))


def conditional_exact(m, k, n, d):
    return Fraction(conditional_numerator(m, k * n, d), m ** (k * n))


def standard_exact(m, k, n):
    counts = distinct_counts(m, k)
    numerator = sum(counts[d] * conditional_numerator(m, k * n, d) for d in range(1, k + 1))
    return Fraction(numerator, m ** (k * n + k))


def dh_positions(m, k, a, b, partitioned=False):
    modulus = m // k if partitioned else m
    offsets = [i * modulus if partitioned else 0 for i in range(k)]
    return tuple(offsets[i] + (a + i * b) % modulus for i in range(k))


def dh_histogram(m, k, query, partitioned=False):
    """Enumerate every insert pair, projecting its hit set onto the query.

    For each step, only starts that hit a query bit need a dictionary entry;
    all remaining starts contribute to the empty hit mask in one integer sum.
    """
    modulus = m // k if partitioned else m
    query = tuple(dict.fromkeys(query))
    histogram = [0] * (1 << len(query))
    for b in range(modulus):
        hits = {}
        for j, q in enumerate(query):
            indices = [q // modulus] if partitioned else range(k)
            for i in indices:
                a = (q % modulus - i * b) % modulus
                hits[a] = hits.get(a, 0) | (1 << j)
        histogram[0] += modulus - len(hits)
        for mask in hits.values():
            histogram[mask] += 1
    return histogram


def avoidance_counts(histogram):
    """Subset zeta transform gives counts avoiding each subset of query bits."""
    counts = list(histogram)
    d = (len(counts) - 1).bit_length()
    for bit in range(d):
        for mask in range(len(counts)):
            if mask & (1 << bit):
                counts[mask] += counts[mask ^ (1 << bit)]
    full = len(counts) - 1
    return [counts[full ^ subset] for subset in range(len(counts))]


def dh_exact(histogram, n):
    counts = avoidance_counts(histogram)
    numerator = sum((-1) ** subset.bit_count() * count ** n for subset, count in enumerate(counts))
    return Fraction(numerator, sum(histogram) ** n)


def step_classes(m):
    return sorted({math.gcd(b, m) for b in range(m)})
