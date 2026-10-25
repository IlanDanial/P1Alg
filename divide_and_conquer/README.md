# Divide and conquer: capped map search via adaptive quadtree

Map-search sites (e.g. Airbnb) only show a limited number of listings per map
window. `quadtree.collect` enumerates every listing by splitting any window that
overflows the cap `k` into four quadrants and recursing.

| File | Purpose |
|---|---|
| `quadtree.py` | The algorithm (`collect`) and half-open `Rect` |
| `test_quadtree.py` | Correctness checks: every listing found once, leaves tile the map, every leaf has at most `k` listings |
| `experiments.py` | Timing experiments; writes `results/*.csv` |
| `plots.py` | Draws `figures/*.pdf|png` from `results/` and the Rincón data |
| `sec_dc.tex`, `app_dc.tex`, `refs.bib` | Report section, appendices (code + LLM log), and citations |
| `main.tex` | Standalone IEEE conference build; header comment explains merging into the group paper |
| `data/rincon_listings.csv` | 261 real listing coordinates (Rincón, PR, scraped 2023-03-29) from [IlanDanial/airbnb_data](https://github.com/IlanDanial/airbnb_data) |

```
python -m unittest test_quadtree   # correctness
python experiments.py              # ~1 minute; writes results/*.csv
python plots.py                    # draws the figures from results/
```

Requires Python 3.9+ with `matplotlib`.

## Analysis being verified

- Uniformly spread listings: `T(n) = 4T(n/4) + Θ(n)`, so `T(n) = Θ(n log(n/k))` (Master theorem, case 2).
- General case: `O(n · h)`, where the tree height `h ≤ log2(W/δ) + 1` depends on how tightly
  listings crowd together (`δ`), not on `n`. Termination needs at most `k` listings at any single
  coordinate. The Rincón data has up to 7 per coordinate because Airbnb rounds locations, so `k ≥ 7`.
