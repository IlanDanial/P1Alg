# Greedy: fewest price refreshes for cruise quote requests

This folder is the greedy half of the COT5405 Project 1 report
([`../report.pdf`](../report.pdf)). It holds the algorithm, the tests, the
experiments behind the report's figures, the real-data case study and the Lean
proof.

**The problem.** A cruise-fare tracker reads Carnival's search endpoint, which
is unofficial and rate-limited, so it should call it as rarely as it can. We let
users ask for one fresh price of a sailing at some point within a window of
days. The tracker then needs the fewest refresh days such that every window
contains one. This is the minimum point cover of a set of intervals.

**The result.** Scan the windows by closing day and, whenever one is not yet
hit, refresh on its last day. This is optimal and runs in `O(n log n)`. On 383
real Florida sailings it needs 3 refreshes over a six-month horizon.

## Files

| File | Purpose |
|---|---|
| `refresh_days.py` | The algorithm (`refresh_days`), the scan alone (`refresh_days_sorted`), and `windows`, which builds quote windows from sailing dates |
| `test_refresh_days.py` | Correctness checks: every window hit, witnesses disjoint, brute-force minimum on small cases, worked example, window construction |
| `fetch_sailings.py` | Downloads Florida sailings for Nov 2026 to Apr 2027 into `data/sailings.csv` and prints the case study |
| `experiments.py` | Timing experiments; writes `results/*.csv` |
| `plots.py` | Draws `figures/*.pdf|png` from `results/` and the sailing data |
| `sec_greedy.tex`, `app_greedy.tex` | Report section and appendices; input by `../report.tex`, citations in `../refs.bib` |
| `proof/` | Lean 4 formalization of Lemma 1, Lemma 2 and Theorem 1 (`lake build` checks it; needs [elan](https://github.com/leanprover/elan)) |
| `appendix/` | Files the report's appendix includes |
| `data/sailings.csv` | 383 real sailings from Miami, Port Canaveral, Tampa and Jacksonville, fetched 2026-10-26 from Carnival's public search |

## Running it

Requires Python 3.9+ with `matplotlib`. Run from this folder:

```
python -m unittest test_refresh_days   # correctness
python experiments.py                  # ~1 minute; writes results/*.csv
python plots.py                        # draws the figures from results/
python fetch_sailings.py               # ~20 s; optional, see below
```

`fetch_sailings.py` re-downloads `data/sailings.csv` from Carnival, so the case
study numbers change as Carnival's listings change. The committed CSV is the
data the report uses; skip this step to reproduce them. The report itself builds
from the repository root (see the [top-level README](../README.md)).

## Case study

Today is 2026-10-26, booking closes `c = 2` days before departure (assumed), and
windows open at Carnival's final-payment deadline (76 days before departure for
cruises of 5 days or fewer, 91 days otherwise). For the 383 sailings that gives
n = 383 windows and m = 3 refresh days (2026-10-30, 2027-01-14, 2027-03-30) over
a 184-day horizon.

## Analysis being verified

- Optimal: the windows that forced a refresh are pairwise disjoint, so any
  schedule needs at least as many days (Theorem 1).
- `O(n log n)` with the sort, `O(n)` for the scan on windows already sorted by
  closing day (Theorem 2). Measured time follows `n log2 n` (R^2 = 0.998);
  per-window cost rises above about 2^18 windows as the input outgrows the CPU
  cache.
