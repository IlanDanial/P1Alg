"""Draw the report's figures from results/*.csv and data/sailings.csv.

Styled like the divide-and-conquer figures (IEEE two-column, Times, 8pt).
Writes figures/*.pdf for LaTeX and figures/*.png for quick viewing.

Run: python plots.py   (after experiments.py has produced results/)
"""

import csv
from datetime import timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments import RESULTS, fit_constant, model
from fetch_sailings import C, TODAY, read_sailings
from refresh_days import refresh_days, windows

HERE = Path(__file__).parent
FIGURES = HERE / "figures"
COLUMN, PAGE = 3.45, 7.1  # IEEE column and text widths in inches
BLUE, RED, GREY = "#1f5f9f", "#c0392b", "#555555"

STYLE = {
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "Times", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 8,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.5,
    "ytick.major.width": 0.5,
    "lines.linewidth": 0.9,
    "lines.markersize": 3.2,
    "grid.linewidth": 0.3,
    "grid.color": "#cccccc",
    "legend.frameon": False,
    "legend.handlelength": 1.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
}


def read_csv(path):
    """Rows as dicts, with integer columns kept as ints."""
    def parse(v):
        return int(v) if v.lstrip("-").isdigit() else float(v)
    with open(path) as f:
        return [{key: parse(v) for key, v in row.items()} for row in csv.DictReader(f)]


def save(fig, name):
    fig.savefig(FIGURES / f"{name}.pdf")
    fig.savefig(FIGURES / f"{name}.png", dpi=250)
    plt.close(fig)


def panel_label(ax, text):
    ax.set_title(text, loc="left", fontweight="bold", pad=4)


def plot_scaling(rows):
    """Time against n with the fitted c n log2 n."""
    fig, ax = plt.subplots(figsize=(PAGE / 3, 1.9))
    ns = [r["n"] for r in rows]
    c, r2 = fit_constant(rows)
    print(f"full: c = {c:.3e} s, R^2 = {r2:.5f}")
    ax.loglog(ns, [r["time_s"] for r in rows], "o", color=BLUE, ls="none", label="measured")
    ax.loglog(ns, [c * model(n) for n in ns], "--", color=GREY, lw=0.8, zorder=1,
              label=r"fit $c\,n\log_2 n$")
    ax.set_xlabel("windows $n$")
    ax.set_ylabel("time (s)")
    ax.legend(loc="lower right")
    ax.grid(True, which="major")
    panel_label(ax, "(a)")
    fig.tight_layout()
    save(fig, "scaling")


def plot_ratio(rows):
    """Time divided by n log2 n; flat means the n log n growth is tight."""
    fig, ax = plt.subplots(figsize=(PAGE / 3, 1.9))
    ns = [r["n"] for r in rows]
    ax.semilogx(ns, [1e9 * r["time_s"] / model(r["n"]) for r in rows], "o", color=BLUE, ls="-")
    ax.set_ylim(bottom=0)
    ax.set_xlabel("windows $n$")
    ax.set_ylabel(r"time / $n\log_2 n$ (ns)")
    ax.grid(True, which="major")
    panel_label(ax, "(b)")
    fig.tight_layout()
    save(fig, "ratio")


def plot_scan(rows, fit_max=2**17):
    """The scan alone on pre-sorted input, with a linear fit.

    The fit uses n <= fit_max only: past that the input outgrows the CPU
    cache and the per-window cost rises (see the report), which would
    otherwise pull a least-squares line off every in-cache point.
    """
    fig, ax = plt.subplots(figsize=(PAGE / 3, 1.9))
    ns = [r["n"] for r in rows]
    c, r2 = fit_constant([r for r in rows if r["n"] <= fit_max], f=lambda n: n)
    print(f"scan (n <= {fit_max}): c = {c:.3e} s, R^2 = {r2:.5f}")
    ax.loglog(ns, [r["time_s"] for r in rows], "s", color=RED, ls="none", label="measured")
    ax.loglog(ns, [c * n for n in ns], "--", color=GREY, lw=0.8, zorder=1, label=r"fit $c\,n$")
    ax.set_xlabel("windows $n$ (pre-sorted)")
    ax.set_ylabel("time (s)")
    ax.legend(loc="lower right")
    ax.grid(True, which="major")
    panel_label(ax, "(c)")
    fig.tight_layout()
    save(fig, "scan")


def plot_windows():
    """Real quote windows sorted by closing day, with the chosen refresh days."""
    iv = sorted(windows(read_sailings(), TODAY, C), key=lambda w: w[1])
    days, wit = refresh_days(iv)
    wit = set(wit)
    fig, ax = plt.subplots(figsize=(COLUMN, 2.6))
    for y, (a, b) in enumerate(iv):
        hit = (a, b) in wit
        ax.plot([a, b], [y, y], color=RED if hit else BLUE, lw=1.4 if hit else 0.35,
                alpha=1 if hit else 0.6, solid_capstyle="butt")
    for t in days:
        ax.axvline(t, color=GREY, lw=0.8, ls="--")
        ax.text(t + 1.5, len(iv) * 1.01, f"{TODAY + timedelta(days=t):%b %d}", ha="left",
                va="bottom", fontsize=6.5)
    ax.set_xlabel(f"days after {TODAY:%b %d, %Y}")
    ax.set_ylabel("sailings, by closing day")
    ax.set_ylim(-2, len(iv) * 1.08)
    ax.set_xlim(left=-3)
    fig.tight_layout()
    save(fig, "windows")
    print(f"windows: n={len(iv)}, refresh days {days}")


def main():
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update(STYLE)
    plot_scaling(read_csv(RESULTS / "scaling.csv"))
    plot_ratio(read_csv(RESULTS / "scaling.csv"))
    plot_scan(read_csv(RESULTS / "scan_only.csv"))
    plot_windows()


if __name__ == "__main__":
    main()
