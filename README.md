# COT5405 Project 1: Greedy and Divide-and-Conquer Algorithms for Real-World Problems

Ilan Danial and Ryan Rodriguez, University of Florida.
The report is [`report.pdf`](report.pdf)

**Greedy ([`greedy/`](greedy/)).**
A cruise-fare tracker reads Carnival's unofficial, rate-limited search endpoint. We propose quote requests,
each asking for one fresh price of a sailing within a window of days, and
choose the fewest refresh batches that serve every window. This is the minimum
point cover of intervals; scanning windows by closing day and refreshing on the
last day of each window not yet served is optimal, proved with a set of
pairwise disjoint witness windows (machine-checked in Lean 4,
`greedy/proof/`), and runs in `O(n log n)`.

**Divide and conquer ([`divide_and_conquer/`](divide_and_conquer/)).**
Map-search sites cap the listings shown per window. An adaptive
quadtree splits any overflowing window into quadrants until every window fits,
collecting every listing with `Θ(n/k)` requests for evenly spread listings and
a recursion depth of at most `⌈log2 W⌉`. Every correctness statement is
machine-checked in Lean 4 (`divide_and_conquer/proof/`).
