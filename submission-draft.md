# [Re] A Case for Partitioned Bloom Filters

**Original article:** Paulo Sérgio Almeida, *A Case for Partitioned Bloom Filters*, IEEE Transactions on Computers 72(6), 1681–1691 (2023). [DOI](https://doi.org/10.1109/TC.2022.3218995) · [Public manuscript](https://arxiv.org/abs/2009.11789v2)

**PDF URL:** https://github.com/tridev-tej/rescience-bloom-replication/blob/a65ee3c2e27c68be5118f24875008b7195458127/manuscript/article.pdf  
**Metadata URL:** https://github.com/tridev-tej/rescience-bloom-replication/blob/a65ee3c2e27c68be5118f24875008b7195458127/manuscript/metadata.yaml  
**Code URL:** https://github.com/tridev-tej/rescience-bloom-replication/tree/a65ee3c2e27c68be5118f24875008b7195458127

**Scientific domain:** Computer Science  
**Programming language:** Python  
**Suggested editor:** No preference

This partial replication of Sections 3–5 recovers the nominal-load mean rates
and fixed-key collision effects. Four printed low-load ratios exceed a bound
valid for every common positive integer insertion count under independent
uniform hashing. Across four original published tables, 99 of 124 printed cell
occurrences match; the artifact retains all 25 differences and adds an exact
double-hashing extension. The scoped experiment runs offline.

Almeida (personal communication, 7 November 2026) reports an off-by-one loop
error and a corrected example that agrees numerically with the independent
calculation. He supplied neither original nor corrected code or tables for
inspection. The reported diagnosis has not been independently reproduced, and
the matching example does not resolve all 25 published-table differences.
