# Scientific source

Paulo Sérgio Almeida, *A Case for Partitioned Bloom Filters*, IEEE Transactions on Computers 72(6), 1681–1691 (2023). [Version of record](https://doi.org/10.1109/TC.2022.3218995) · [Public accepted manuscript, v2](https://arxiv.org/abs/2009.11789v2).

- Source examined: `https://arxiv.org/pdf/2009.11789v2`. PDF SHA-256 `abaf3b485ca50390450f189c3d18132eae45ca6ac6365a07bb4cb7fa902001dd`.
- Table values were transcribed from pages 4–6 into `replication/published.py`. The code derives predictions independently of the source values. No external data or author code are needed at runtime.
- Almeida (personal communication, 7 November 2026) reports an off-by-one loop error and a corrected example that agrees numerically with the independent calculation. He supplied neither original nor corrected code or tables for inspection. His diagnosis has not been independently reproduced. The comparison retains all 25 differences against the original published tables.
- Source Figure 3 gives a size sweep. The reconstructed curves use a grid of valid partition sizes and do not digitize the published curves. Source Figure 4 gives an inverse tail. The full output includes all collision classes, including those below the plot's display cutoff.
- The double-hashing calculation at 512 bits and 44 insertions is an extension. Only the structural witnesses correspond to published figures.
