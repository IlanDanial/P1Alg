"""Draw the report's figures from results/*.csv and data/rincon_listings.csv.

Styled for an IEEE two-column paper (Times, 10pt body text). Writes
figures/*.pdf for LaTeX and figures/*.png for quick viewing.

Run: python plots.py   (after experiments.py has produced results/)
"""

import csv
import math
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from experiments import K, RESULTS, model, fit_constant
from quadtree import Rect, bounding_rect, collect

HERE = Path(__file__).parent
FIGURES = HERE / "figures"
COLUMN, PAGE = 3.45, 7.1  # IEEE column and text widths in inches
BLUE, RED, GREY = "#1f5f9f", "#c0392b", "#555555"
SERIES = [("uniform", "o", BLUE), ("clustered", "s", RED)]  # label, marker, color

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


def plot_scaling(uni, clu):
    """Three panels: time with fitted model, normalized time, request count."""
    fig, (ax_t, ax_r, ax_q) = plt.subplots(1, 3, figsize=(PAGE, 2.05))
    ns = [r["n"] for r in uni]

    for rows, (label, marker, color) in zip((uni, clu), SERIES):
        c, r2 = fit_constant(rows)
        print(f"{label}: c = {c:.3e} s, R^2 = {r2:.5f}")
        ax_t.loglog(ns, [r["time_s"] for r in rows], marker, color=color, ls="none", label=label)
        ax_t.loglog(ns, [c * model(n) for n in ns], "--", color=GREY, lw=0.8, zorder=1)
        ax_r.semilogx(ns, [1e9 * r["time_s"] / model(r["n"]) for r in rows],
                      marker, color=color, ls="-", label=label)
        ax_q.loglog(ns, [r["queries"] for r in rows], marker, color=color, ls="none", label=label)

    ax_t.plot([], [], "--", color=GREY, lw=0.8, label=r"fit $c\,n\log_2(n/k)$")
    ax_t.set_ylabel("time (s)")
    ax_t.legend(loc="upper left")
    panel_label(ax_t, "(a)")

    ax_r.set_ylabel("normalized time (ns)")
    ax_r.set_ylim(0, 60)
    panel_label(ax_r, "(b)")

    ax_q.loglog(ns, [n / K for n in ns], "-", color=GREY, lw=0.8, label="lower bound $n/k$")
    ax_q.set_ylabel("search requests")
    ax_q.legend(loc="upper left")
    panel_label(ax_q, "(c)")

    for ax in (ax_t, ax_r, ax_q):
        ax.set_xlabel("number of listings $n$")
        ax.grid(True, which="major")
    fig.tight_layout(w_pad=1.5)
    save(fig, "scaling")


def plot_depth(rows):
    """Two panels: tree height and request count as listings crowd together."""
    fig, (ax_h, ax_q) = plt.subplots(1, 2, figsize=(COLUMN, 1.75))
    xs = [r["log2_inv_delta"] for r in rows]

    ax_h.plot(xs, xs, "-", color=GREY, lw=0.8, label=r"$\log_2(1/\delta)$")
    ax_h.plot(xs, [r["max_depth"] for r in rows], "o", color=BLUE, label="measured")
    ax_h.set_ylabel("tree height")
    ax_h.legend(loc="upper left")
    panel_label(ax_h, "(a)")

    ax_q.plot(xs, [r["queries"] for r in rows], "s", color=RED, ls="-")
    ax_q.set_ylabel("search requests")
    panel_label(ax_q, "(b)")

    for ax in (ax_h, ax_q):
        ax.set_xlabel(r"$\log_2(1/\delta)$")
        ax.set_xticks([0, 10, 20, 30])
        ax.grid(True)
    fig.tight_layout(w_pad=1.5)
    save(fig, "depth_vs_delta")


def plot_rincon(k=20):
    """The windows collect() chooses for the real Rincon listings.

    k is 20 rather than K=50 because with only 261 listings a cap of 50
    would split the map just a few times and show little of the structure.
    """
    with open(HERE / "data" / "rincon_listings.csv") as f:
        pts = [(float(r["lng"]), float(r["lat"])) for r in csv.DictReader(f)]
    # Pad the map window a little so edge listings do not sit on its border.
    box = bounding_rect(pts)
    pad_x, pad_y = 0.02 * (box.x1 - box.x0), 0.02 * (box.y1 - box.y0)
    root = Rect(box.x0 - pad_x, box.y0 - pad_y, box.x1 + pad_x, box.y1 + pad_y)
    result = collect(root, pts, k)
    assert result.unresolved == 0 and Counter(result.points) == Counter(pts)

    fig, ax = plt.subplots(figsize=(2.45, 2.9))  # narrow: the town is taller than wide
    for r in result.leaves:
        ax.add_patch(Rectangle((r.x0, r.y0), r.x1 - r.x0, r.y1 - r.y0,
                               fill=False, lw=0.45, edgecolor=BLUE))
    ax.plot([p[0] for p in pts], [p[1] for p in pts], ".", ms=2.2, color=RED, ls="none")
    ax.set_xlim(root.x0, root.x1)
    ax.set_ylim(root.y0, root.y1)
    # One degree of longitude is shorter than one of latitude at this latitude.
    mid_lat = math.radians((root.y0 + root.y1) / 2)
    ax.set_aspect(1 / math.cos(mid_lat))
    ax.set_xlabel("longitude ($^\\circ$)")
    ax.set_ylabel("latitude ($^\\circ$)")
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    fig.tight_layout()
    save(fig, "rincon_quadtree")
    print(f"rincon: {len(pts)} listings, {result.queries} requests, "
          f"{len(result.leaves)} windows, height {result.max_depth}")


def main():
    FIGURES.mkdir(exist_ok=True)
    plt.rcParams.update(STYLE)
    plot_scaling(read_csv(RESULTS / "scaling_uniform.csv"),
                 read_csv(RESULTS / "scaling_clustered.csv"))
    plot_depth(read_csv(RESULTS / "depth_vs_delta.csv"))
    plot_rincon()


if __name__ == "__main__":
    main()
