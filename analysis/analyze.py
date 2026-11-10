"""
Analysis of the Bubble Algorithm Library experiment.

Descriptive statistics used: median, range (min to max), mean and standard
deviation; the medians are shown in a bar chart.

Reads results/run*.csv and writes to results/analysis/:
  - descriptive_stats.csv  n, median, min, max, range, mean, standard deviation per condition
  - median_range_tables.md median and range per condition (tables for report section 3.2)
  - run_medians.csv        median per condition and run (checks for differences between runs)
  - growth_factors.csv     how many times the median grows when the array is 10 times larger
  - medians_bar_chart.png  bar chart of the medians, one panel per array size

Usage: python3 analysis/analyze.py
"""

import glob
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ALGORITHMS = ["PASS_PER_ITEM", "UNTIL_NO_CHANGE", "WHILE_NEEDED"]
ORDERS = ["SORTED", "REVERSED", "RANDOM", "NEARLY_SORTED"]
SIZES = [10, 100, 1000, 10000]
NAMES = {"PASS_PER_ITEM": "PassPerItem", "UNTIL_NO_CHANGE": "UntilNoChange", "WHILE_NEEDED": "WhileNeeded",
         "SORTED": "Sorted", "REVERSED": "Reversed", "RANDOM": "Random", "NEARLY_SORTED": "Almost sorted"}
COLORS = {"PASS_PER_ITEM": "#1f77b4", "UNTIL_NO_CHANGE": "#ff7f0e", "WHILE_NEEDED": "#2ca02c"}
# Times of 10 numbers are shown in ns, all other sizes in µs
UNITS = {10: ("ns", 1000), 100: ("µs", 1), 1000: ("µs", 1), 10000: ("µs", 1)}
KEYS = ["algorithm", "size", "order"]
OUT = Path("results/analysis")


def describe(times):
    """Descriptive statistics of the execution times of one condition (µs)."""
    return pd.Series({
        "n": len(times), "median": times.median(), "min": times.min(), "max": times.max(),
        "range": times.max() - times.min(), "mean": times.mean(), "sd": times.std(),
    })


def fmt(value):
    """Three significant digits (keeping trailing zeros), with thousands separators for large values."""
    return f"{value:,.0f}" if value >= 100 else f"{value:#.3g}"


def write_median_range_tables(stats):
    """One Markdown table per array size: median and range (min to max)."""
    lines = []
    for number, size in enumerate(SIZES, start=1):
        unit, factor = UNITS[size]
        lines += [f"**Table {number}: {size:,} numbers (times in {unit})**", "",
                  "| Order | Algorithm | Median | Range (min – max) |", "|---|---|---|---|"]
        for order in ORDERS:
            for algorithm in ALGORITHMS:
                row = stats.loc[(algorithm, size, order)] * factor
                lines.append(f"| {NAMES[order]} | {NAMES[algorithm]} | {fmt(row['median'])} "
                             f"| {fmt(row['min'])} – {fmt(row['max'])} |")
        lines.append("")
    (OUT / "median_range_tables.md").write_text("\n".join(lines), encoding="utf-8")


def write_growth_factors(stats):
    """Median at size n divided by the median at size n/10 (checks the quadratic growth of H4)."""
    medians = stats["median"].unstack("size")[SIZES]
    growth = pd.DataFrame({f"{small}->{large}": medians[large] / medians[small]
                           for small, large in zip(SIZES, SIZES[1:])})
    growth.to_csv(OUT / "growth_factors.csv", float_format="%.1f")


def plot_medians(stats):
    """Bar chart of the median time per sort: one panel per array size, bars grouped by initial order."""
    plt.rcParams.update({"font.size": 12})
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    width = 0.27
    for ax, size in zip(axes.flat, SIZES):
        unit, factor = UNITS[size]
        for a, algorithm in enumerate(ALGORITHMS):
            medians = [stats.loc[(algorithm, size, order), "median"] * factor for order in ORDERS]
            positions = [o + (a - 1) * width for o in range(len(ORDERS))]
            ax.bar(positions, medians, width, color=COLORS[algorithm], label=NAMES[algorithm])
        ax.set_xticks(range(len(ORDERS)))
        ax.set_xticklabels([NAMES[o].replace(" ", "\n") for o in ORDERS], fontsize=10)
        ax.set_ylabel(f"Median time ({unit})")
        ax.set_title(f"{size:,} numbers")
        ax.yaxis.set_major_formatter("{x:,g}")
        ax.grid(axis="y", alpha=0.3)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(OUT / "medians_bar_chart.png", dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = pd.concat([pd.read_csv(path) for path in sorted(glob.glob("results/run*.csv"))])
    data["us"] = data["batch_ns"] / data["batch_size"] / 1000  # time per sort in µs

    stats = data.groupby(KEYS)["us"].apply(describe).unstack()
    stats.to_csv(OUT / "descriptive_stats.csv", float_format="%.4f")

    run_medians = data.groupby(KEYS + ["run"])["us"].median().unstack("run").add_prefix("median_run")
    run_medians.to_csv(OUT / "run_medians.csv", float_format="%.4f")

    write_median_range_tables(stats)
    write_growth_factors(stats)
    plot_medians(stats)
    print(f"Wrote statistics for {len(stats)} conditions ({len(data)} measurements) to {OUT}/")


if __name__ == "__main__":
    main()
