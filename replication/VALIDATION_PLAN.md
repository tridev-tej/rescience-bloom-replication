# Validation plan fixed before implementation and execution

Scope: original, offline, Python standard-library implementation of Sections 3–5
of Almeida's accepted manuscript. The supplied `../PROTOCOL.md` governs.
No upstream implementation, digitized curves, manuscript changes, or public work.

## Locked choices

- Primary insertion count: `floor(occupation * m * log(2) / k)`, inferred because
  the paper prints a real-valued capacity without an integer convention.
- Table comparisons: half of the last printed decimal, plus `1e-12` absolute
  numerical allowance. Compare all 124 numeric cells, including ratio duplicates.
- Figure 3: every multiple of k in [64, 4096], k = 4, 8, 12, 16.
- Figure 4: all collision classes, for (64,4), (64,8), (512,4), (512,8), (512,16).
  Tail means `P(per-element/global >= the reported class ratio)`.
- Simulation: 120000 independent insertion worlds per load, at m=64,k=4,
  occupations 1/4, 1/2, 1/1. `random.Random(20261107 + load_index)` with loads
  in that order. Fixed queries use physical bits 0 through d-1, d=1..4;
  these queries are paired within a world. At full load also draw a fresh iid
  random query in each SBF world. PBF uses separate worlds and seed 20261110.
- Wilson intervals use z=1.959963984540054. Descriptive calibration passes iff
  max absolute binomial standardized error <=4.5 among cells with both expected
  hits and misses >=20. Report every cell, including rare cells. No rerolls.
- DH extension: m=512,k=8,n=floor(512*log(2)/8), uniform independent insert
  pairs over all residues including zero steps. SBF covers every gcd class;
  PBF uses modulus 64 with ordered, physically disjoint parts. Integer counts
  and exact rational inclusion-exclusion, with no floating-point cancellation.
- Deterministic outputs contain no timings, execution timestamps, or machine data.
  Execution measurements and environment metadata go in `measurements/` only.

## Checks to implement before the science

1. Enumerate all m=4,k=2,n=2 iid insertion sequences and query sequences.
   Compare the global and fixed-distinct-query rates with the forward recurrence,
   integer inclusion-exclusion, and iid partitioned formula.
2. Exhaustively enumerate DH insertion-pair sequences at that tiny size and every
   possible fixed query pair for both layouts; compare exact rational rates.
3. Require empty-filter rates zero, probabilities in [0,1], normalized query and
   state distributions, and rates nonincreasing in number of distinct query bits.
4. Cross-check every distinct-query conditional rate and the global rate on the
   complete table/load grid with an independent integer inclusion-exclusion oracle.
5. Check DH histogram integer totals, subset avoidance counts, class weights,
   translation/odd-unit representatives, PBF query symmetry, and exact one-bit
   coverage from mean distinct positions per inserted DH element.
6. Assert physical-bit counts and overlaps for repetition, reversal, and shift
   witnesses at the same total allocation m=512,k=8.
7. Check the full generated CSVs, TeX and SVGs; run the complete pipeline twice
   and require identical hashes for all deterministic result files.
8. Measure every Python function and expression scope. No inline code comments;
   no function above CC10. Analyzer/proof helpers are included.

Published mismatches remain data, not broken assertions. Any mismatch triggers
only the predeclared floor/nearest/ceil diagnostic; it never changes primary
results or comparison tolerance. A failed science invariant exits nonzero.
Protocol deviations will be recorded explicitly after execution, including none.
