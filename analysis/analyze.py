"""
Analysis of the Bubble Algorithm Library experiment.

Reads results/run*.csv and writes to results/analysis/:
  - descriptive_stats.csv  descriptive statistics per configuration (all runs together)
  - run_medians.csv        median per configuration and run (checks for differences between runs)
  - five_number_summary.md min, Q1, median, Q3, max per condition (table for report section 3.2)
  - boxplot_n<size>.png    box plots per array size
  - scaling_loglog.png     median time vs array size (log-log)

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
COLORS = {"PASS_PER_ITEM": "#1f77b4", "UNTIL_NO_CHANGE": "#ff7f0e", "WHILE_NEEDED": "#2ca02c"}
# Different markers and line styles, so lines with (almost) equal values stay visible
STYLES = {"PASS_PER_ITEM": ("o", "-"), "UNTIL_NO_CHANGE": ("s", "--"), "WHILE_NEEDED": ("^", ":")}
KEYS = ["algorithm", "size", "order"]
OUT = Path("results/analysis")


def describe(times):
    """Descriptive statistics of a series of execution times (µs)."""
    mean, sd, n = times.mean(), times.std(), len(times)
    return pd.Series({
        "n": n, "mean": mean, "sd": sd, "cv_percent": 100 * sd / mean,
        "min": times.min(), "q1": times.quantile(0.25), "median": times.median(),
        "q3": times.quantile(0.75), "max": times.max(),
        "ci95_low": mean - 1.96 * sd / n ** 0.5, "ci95_high": mean + 1.96 * sd / n ** 0.5,
    })


def plot_boxplots(data):
    """One figure per array size: box plots grouped by order and coloured by algorithm."""
    for size in sorted(data["size"].unique()):
        subset = data[data["size"] == size]
        fig, ax = plt.subplots(figsize=(10, 5))
        for a, algorithm in enumerate(ALGORITHMS):
            values = [subset[(subset["order"] == o) & (subset["algorithm"] == algorithm)]["us"] for o in ORDERS]
            box = ax.boxplot(values, positions=[o + (a - 1) * 0.25 for o in range(len(ORDERS))],
                             widths=0.22, patch_artist=True, flierprops={"markersize": 3},
                             medianprops={"color": "black"})
            for patch in box["boxes"]:
                patch.set_facecolor(COLORS[algorithm])
                patch.set_edgecolor(COLORS[algorithm])  # flat boxes still show their colour
                patch.set_linewidth(2)
            ax.plot([], [], color=COLORS[algorithm], linewidth=8, label=algorithm)
        ax.set_xticks(range(len(ORDERS)))
        ax.set_xticklabels(ORDERS)
        ax.set_yscale("log")
        ax.set_ylabel("Execution time per sort (µs, log scale)")
        ax.set_xlabel("Initial order of the data")
        ax.set_title(f"Execution time by algorithm and initial order, n = {size}")
        ax.legend()
        ax.grid(axis="y", which="both", alpha=0.3)
        fig.tight_layout()
        fig.savefig(OUT / f"boxplot_n{size}.png", dpi=150)
        plt.close(fig)


def plot_scaling(stats):
    """Log-log plot of median time vs array size, one panel per initial order."""
    fig, axes = plt.subplots(1, len(ORDERS), figsize=(16, 4.5), sharey=True)
    for ax, order in zip(axes, ORDERS):
        for algorithm in ALGORITHMS:
            line = stats[(stats["order"] == order) & (stats["algorithm"] == algorithm)].sort_values("size")
            marker, linestyle = STYLES[algorithm]
            ax.plot(line["size"], line["median"], marker=marker, linestyle=linestyle, markersize=7,
                    markerfacecolor="none", markeredgewidth=1.5, color=COLORS[algorithm], label=algorithm)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(order)
        ax.set_xlabel("Array size n (log)")
        ax.grid(which="both", alpha=0.3)
    axes[0].set_ylabel("Median time per sort (µs, log)")
    axes[-1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "scaling_loglog.png", dpi=150)
    plt.close(fig)


def write_five_number_summary(stats):
    """Markdown table (min, Q1, median, Q3, max in µs) per condition, ready to paste into the report."""
    lines = ["| Size | Order | Algorithm | Min | Q1 | Median | Q3 | Max |", "|---|---|---|---|---|---|---|---|"]
    for size in sorted(stats["size"].unique()):
        for order in ORDERS:
            for algorithm in ALGORITHMS:
                row = stats[(stats["size"] == size) & (stats["order"] == order) & (stats["algorithm"] == algorithm)]
                if row.empty:
                    continue
                row = row.iloc[0]
                values = " | ".join(f"{row[c]:.3g}" for c in ["min", "q1", "median", "q3", "max"])
                lines.append(f"| {size} | {order} | {algorithm} | {values} |")
    (OUT / "five_number_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = pd.concat([pd.read_csv(path) for path in sorted(glob.glob("results/run*.csv"))])
    data["us"] = data["batch_ns"] / data["batch_size"] / 1000  # time per sort in µs

    stats = data.groupby(KEYS)["us"].apply(describe).unstack().reset_index()
    stats.to_csv(OUT / "descriptive_stats.csv", index=False, float_format="%.4f")

    run_medians = data.groupby(KEYS + ["run"])["us"].median().unstack("run").add_prefix("median_run")
    run_medians.to_csv(OUT / "run_medians.csv", float_format="%.4f")

    write_five_number_summary(stats)
    plot_boxplots(data)
    plot_scaling(stats)
    print(f"Wrote statistics for {len(stats)} configurations ({len(data)} measurements) to {OUT}/")


if __name__ == "__main__":
    main()
