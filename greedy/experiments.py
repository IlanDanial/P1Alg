"""Running-time experiments for refresh_days.

Two experiments, each written to results/*.csv:
  scaling.csv    full algorithm (sort + scan) as n grows
  scan_only.csv  the scan alone on windows already sorted by closing day
plots.py turns the CSV files into the figures in the report.

Run: python experiments.py   (a few minutes)
"""

import bisect
import csv
import gc
import math
import random
import statistics
import time
from pathlib import Path

from fetch_sailings import C, read_sailings
from refresh_days import final_payment_days, refresh_days, refresh_days_sorted

RESULTS = Path(__file__).parent / "results"
SIZES = [2**e for e in range(10, 23)]  # 1,024 .. 4,194,304 windows
TRIALS = 5  # random inputs per size


# -- inputs -----------------------------------------------------------------

def nights_mix():
    """Cruise lengths of the real sailings, sampled to give realistic windows."""
    return [s["nights"] for s in read_sailings()]


def random_windows(n, rng, mix):
    """n quote windows for sailings departing uniformly over 2n days.

    The horizon grows with n so closing days stay mostly distinct; a fixed
    horizon would make most windows tie and measure something else.
    """
    out = []
    for _ in range(n):
        d = rng.randrange(2 * n)
        out.append((d - final_payment_days(rng.choice(mix)), d - C))
    return out


# -- predictions from the analysis -------------------------------------------

def model(n):
    """Predicted work n log2 n for the comparison sort (Theorem 2)."""
    return n * math.log2(n)


def fit_constant(rows, f=model):
    """Least-squares c for time = c * f(n) over the rows, and the fit's R^2."""
    fs = [f(r["n"]) for r in rows]
    t = [r["time_s"] for r in rows]
    c = sum(a * b for a, b in zip(fs, t)) / sum(a * a for a in fs)
    mean = statistics.mean(t)
    ss_res = sum((ti - c * fi) ** 2 for fi, ti in zip(fs, t))
    ss_tot = sum((ti - mean) ** 2 for ti in t)
    return c, 1 - ss_res / ss_tot


# -- measurement -------------------------------------------------------------

def timed(fn, arg):
    """Time fn(arg) with the garbage collector off, as timeit does."""
    gc.collect()
    gc.disable()
    try:
        start = time.perf_counter()
        out = fn(arg)
        elapsed = time.perf_counter() - start
    finally:
        gc.enable()
    return elapsed, out


def check(iv, days, witnesses):
    """Every window holds a chosen day (Lemma 1); one witness per day (Lemma 2)."""
    assert len(witnesses) == len(days)
    for a, b in iv:
        i = bisect.bisect_left(days, a)  # days come out increasing
        assert i < len(days) and days[i] <= b
    for (_, b1), (a2, _) in zip(witnesses, witnesses[1:]):
        assert b1 < a2


def run(mix):
    """Time refresh_days and the scan alone for each n on TRIALS fresh inputs.

    Reports the fastest time of each (the least-disturbed run, as timeit
    recommends) and the median number of refresh days.
    """
    full, scan = [], []
    for n in SIZES:
        t_full, t_scan, ms = [], [], []
        for t in range(TRIALS):
            iv = random_windows(n, random.Random(1000 * n + t), mix)
            elapsed, (days, witnesses) = timed(refresh_days, iv)
            check(iv, days, witnesses)
            t_full.append(elapsed)
            ms.append(len(days))
            iv.sort(key=lambda w: w[1])
            elapsed, sdays = timed(refresh_days_sorted, iv)
            assert sdays == days
            t_scan.append(elapsed)
        m = int(statistics.median(ms))
        full.append({"n": n, "time_s": min(t_full), "refresh_days": m})
        scan.append({"n": n, "time_s": min(t_scan), "refresh_days": m})
        print(f"n={n:8d}  full={min(t_full):.4f}s  scan={min(t_scan):.4f}s  m={m}")
    write_csv(RESULTS / "scaling.csv", full)
    write_csv(RESULTS / "scan_only.csv", scan)


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    run(nights_mix())
