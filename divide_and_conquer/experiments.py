"""Running-time experiments for quadtree.collect.

Three experiments, each written to results/*.csv:
  scaling_uniform.csv, scaling_clustered.csv  time, requests and tree height
                                              as n grows (balanced case)
  depth_vs_delta.csv                          tree height as k+1 listings are
                                              packed ever closer together
plots.py turns the CSV files into the figures in the report.

Run: python experiments.py   (about a minute)
"""

import csv
import gc
import math
import random
import statistics
import time
from collections import Counter
from pathlib import Path

from quadtree import Rect, collect

RESULTS = Path(__file__).parent / "results"
K = 50  # listings a search shows before truncating (a few result pages)
SIZES = [2**e for e in range(10, 20)]  # 1,024 .. 524,288 listings
TRIALS = 5  # random inputs per size
UNIT = Rect(0.0, 0.0, 1.0, 1.0)


# -- inputs -----------------------------------------------------------------

def uniform(n, rng):
    """n listings spread evenly over the unit square."""
    return [(rng.random(), rng.random()) for _ in range(n)]


def clustered(n, rng, centers=20, spread=0.02):
    """n listings concentrated around a few neighborhoods (Gaussian clusters)."""
    cs = [(rng.random(), rng.random()) for _ in range(centers)]
    pts = []
    while len(pts) < n:
        cx, cy = rng.choice(cs)
        x, y = rng.gauss(cx, spread), rng.gauss(cy, spread)
        if 0.0 <= x < 1.0 and 0.0 <= y < 1.0:
            pts.append((x, y))
    return pts


# -- predictions from the analysis -------------------------------------------

def model(n):
    """Predicted work n log2(n/k), from T(n) = 4T(n/4) + Theta(n)."""
    return n * math.log2(n / K)


def balanced_queries(n):
    """Requests when every split is even: a complete 4-ary tree of L+1 levels."""
    levels = 0
    while K * 4**levels < n:
        levels += 1
    return (4 ** (levels + 1) - 1) // 3


def fit_constant(rows):
    """Least-squares c for time = c * model(n) over the rows, and the fit's R^2."""
    f = [model(r["n"]) for r in rows]
    t = [r["time_s"] for r in rows]
    c = sum(a * b for a, b in zip(f, t)) / sum(a * a for a in f)
    mean = statistics.mean(t)
    ss_res = sum((ti - c * fi) ** 2 for fi, ti in zip(f, t))
    ss_tot = sum((ti - mean) ** 2 for ti in t)
    return c, 1 - ss_res / ss_tot


# -- measurement -------------------------------------------------------------

def time_collect(pts):
    """Time collect() on pts, then check it returned every listing exactly once."""
    # Like timeit, keep the garbage collector from adding pauses to the timing.
    gc.collect()
    gc.disable()
    try:
        start = time.perf_counter()
        result = collect(UNIT, pts, K)
        elapsed = time.perf_counter() - start
    finally:
        gc.enable()
    assert result.unresolved == 0 and Counter(result.points) == Counter(pts)
    return elapsed, result


def run_scaling(name, gen):
    """Time collect() for each n in SIZES on TRIALS fresh inputs from gen.

    Reports the fastest time (the least-disturbed run, as timeit recommends)
    and the median request count and tree height.
    """
    rows = []
    for n in SIZES:
        times, queries, depths = [], [], []
        for t in range(TRIALS):
            pts = gen(n, random.Random(1000 * n + t))
            elapsed, result = time_collect(pts)
            times.append(elapsed)
            queries.append(result.queries)
            depths.append(result.max_depth)
        row = {
            "n": n,
            "time_s": min(times),
            "queries": int(statistics.median(queries)),
            "balanced_queries": balanced_queries(n),
            "max_depth": int(statistics.median(depths)),
        }
        rows.append(row)
        print(f"{name:9s} n={n:7d}  time={row['time_s']:.4f}s  "
              f"queries={row['queries']}  depth={row['max_depth']}")
    write_csv(RESULTS / f"scaling_{name}.csv", rows)
    return rows


def run_depth(n=10_000, seed=7):
    """Pack k+1 listings (a 'building') into a square of side delta = 2^-e.

    n stays fixed, so any growth in height and requests comes from the
    crowding alone. The building is placed away from the map's edges so the
    quadrants that isolate it are not clipped by the border.
    """
    rows = []
    for e in range(2, 29, 2):  # stays above collect's min_width of 1e-9 ~ 2^-30
        delta = 2.0**-e
        rng = random.Random(seed)
        pts = uniform(n - (K + 1), rng)
        cx, cy = 0.3 + 0.4 * rng.random(), 0.3 + 0.4 * rng.random()
        pts += [(cx + delta * rng.random(), cy + delta * rng.random()) for _ in range(K + 1)]
        elapsed, result = time_collect(pts)
        rows.append({"log2_inv_delta": e, "time_s": elapsed,
                     "queries": result.queries, "max_depth": result.max_depth})
        print(f"depth     delta=2^-{e:<2d} queries={result.queries}  depth={result.max_depth}")
    write_csv(RESULTS / "depth_vs_delta.csv", rows)
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    run_scaling("uniform", uniform)
    run_scaling("clustered", clustered)
    run_depth()
