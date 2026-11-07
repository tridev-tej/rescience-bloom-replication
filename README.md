# [Re] A Case for Partitioned Bloom Filters

A partial replication of Almeida's finite-size results in Sections 3–5.
Under independent uniform hashing, four partitioned-to-standard mean
false-positive ratios in Table 2 exceed an upper bound valid for every common
positive integer insertion count in both layouts. These are the quarter- and
half-nominal-load values at 64 bits with four or eight probes. Integer rounding
cannot explain these printed values.

Almeida (personal communication, 7 November 2026) reports an off-by-one loop
error and a corrected example that agrees numerically with the independent
calculation. He supplied neither original nor corrected code or tables for
inspection. The reported diagnosis has not been independently reproduced.
All 25 differences against the original published tables remain recorded.

The calculation recovers the nominal-load mean rates and the concentration of
false positives among keys with repeated probes. An exact double-hashing
extension at 512 bits, eight probes, and 44 insertions finds a 49.81% rate for
zero-step standard queries. Partitioning removes step-dependent variation in
the uniform hash-pair model and raises the mean rate from 0.649% to 1.442%.
Read [the manuscript](manuscript/article.pdf) or start with the
[original paper and source record](SOURCE.md).

## Rerun the experiment

From the directory containing this README:

```sh
(cd replication && python3 replicate.py)
```

Python 3.11 or later. The experiment uses only the standard library and requires
no network, packages, data download, or LaTeX. It checks the formulas against
an exact integer oracle and small exhaustive enumerations. An invariant or
calibration failure exits nonzero. Differences from the source's printed values
are scientific results, so the program records them without changing the
success criteria.

Across four original published tables, 99 of 124 printed cell occurrences
match at the reported precision:

| Source | Cells | Match at printed precision | Differ |
| --- | ---: | ---: | ---: |
| Table 1 | 32 | 31 | 1 |
| Table 2 | 24 | 16 | 8 |
| Table 3 | 48 | 32 | 16 |
| Table 4 | 20 | 20 | 0 |
| Total | 124 | 99 | 25 |

Ratios repeated from Table 1 in Table 2 are counted in both tables. The
[protocol](PROTOCOL.md) and [validation plan](replication/VALIDATION_PLAN.md)
record the evaluation criteria and scope. The floor convention is inferred from
the source's printed nominal-load values.

| File in `replication/results/` | What it contains |
| --- | --- |
| `table_comparison.csv`, `discrepancies.csv` | Every transcribed and recomputed cell, signed difference, and tolerance |
| `insertion_diagnostics.csv`, `rounding_diagnostics.csv` | Inferred nominal counts and floor, nearest, and ceiling comparisons |
| `figure3.csv`, `figure4.csv`, `figure3.svg`, `figure4.svg` | Reconstructed curves and their full data |
| `monte_carlo.csv` | Trial counts, observed rates, exact predictions, Wilson intervals, and calibration errors |
| `dh_classes.csv`, `dh_summary.json` | Exact double-hashing probabilities, with rational numerators and denominators |
| `dh_projected_counts.csv`, `dh_witnesses.csv` | Integer mask counts and physical-address witnesses |
| `summary.json`, `run_summary.txt` | Run and validation outcomes |
| `provenance.json`, `sha256.json` | Source hashes and deterministic output hashes |

The double-hashing probability sweep is a new calculation. The paper's
Figures 5–7 supply the structural mechanisms it tests. Runtime and interpreter
metadata go to `replication/measurements/` and do not affect result hashes.

## Rebuild the PDF

Run this from the directory containing the README, after the experiment:

```sh
SOURCE_DATE_EPOCH=1794096000 FORCE_SOURCE_DATE=1 make -C manuscript
```

The PDF build needs XeLaTeX, Biber matched to the installed BibLaTeX, Make,
`rsvg-convert`, PyYAML in the Python environment, and an installed `en_US.UTF-8`
locale. The metadata helper sets this locale explicitly and fails if it is
unavailable. A full TeX Live installation includes the TeX packages.

The recipe above was tested with XeLaTeX/TeX Live 2025, Biber 2.21,
Python 3.14.7 with PyYAML 6.0.3, and `rsvg-convert` 2.61.3. The PDF build reads
the regenerated experiment CSVs and SVGs. The [metadata](manuscript/metadata.yaml)
follows the journal's schema. Its publication fields are reserved for the
editorial process.

The manuscript uses the [ReScience C template](https://github.com/ReScience/template/tree/0978d0e5d9a86246789fd3468aec6fc71e39c944).
Template changes mark the pre-submission status, render the ORCID badge with
standard LaTeX color boxes, and correct the Python literal used to escape
ampersands in the abstract. The template and fonts retain their upstream licenses.
The Python replication code is available under the [MIT License](replication/LICENSE).
The submission draft is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
