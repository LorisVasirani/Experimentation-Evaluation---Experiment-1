"""
Analysis of the bubble sort experiment.

Reads the raw measurements (results/run1.csv ... run5.csv) and writes to results/analysis/:
  - descriptive_stats.csv   median, min and max of each condition
  - median_range_tables.md  the same numbers as Tables 1-4 of the report
  - run_medians.csv         median of each condition in each of the 5 runs
  - growth_factors.csv      how many times the median grows when the array is 10 times larger
  - medians_bar_chart.png   bar chart of the medians (Figure in section 3.1 of the report)

Usage: python3 analysis/analyze.py
"""

import glob

import matplotlib
matplotlib.use("Agg")  # save the chart to a file instead of opening a window
import matplotlib.pyplot as plt
import pandas as pd

OUT = "results/analysis/"
ALGORITHMS = ["PASS_PER_ITEM", "UNTIL_NO_CHANGE", "WHILE_NEEDED"]
ORDERS = ["SORTED", "REVERSED", "RANDOM", "NEARLY_SORTED"]
SIZES = [10, 100, 1000, 10000]
NAMES = {"PASS_PER_ITEM": "PassPerItem", "UNTIL_NO_CHANGE": "UntilNoChange", "WHILE_NEEDED": "WhileNeeded",
         "SORTED": "Sorted", "REVERSED": "Reversed", "RANDOM": "Random", "NEARLY_SORTED": "Almost sorted"}
COLORS = {"PASS_PER_ITEM": "#1f77b4", "UNTIL_NO_CHANGE": "#ff7f0e", "WHILE_NEEDED": "#2ca02c"}


def unit(size):
    """Arrays of 10 numbers are so fast that their times are shown in ns; all others in µs."""
    return ("ns", 1000) if size == 10 else ("µs", 1)


def fmt(value):
    """Writes a number with 3 significant digits (e.g. 9.32, 0.0862) or as an integer (e.g. 1,112)."""
    return f"{value:,.0f}" if value >= 100 else f"{value:#.3g}"


# Step 1: read the 5 CSV files (one per run) into one table.
# Each row is one batch: run, algorithm, size, order, batch_size (number of sorts), batch_ns (time of the batch).
data = pd.concat([pd.read_csv(file) for file in sorted(glob.glob("results/run*.csv"))])

# Step 2: time of one sort, in µs = time of the batch / number of sorts in the batch / 1000.
data["us"] = data["batch_ns"] / data["batch_size"] / 1000

# Step 3: for each of the 48 conditions (algorithm, size, order), the median, min and max of its 150 times.
stats = data.groupby(["algorithm", "size", "order"])["us"].agg(["median", "min", "max"])
stats.to_csv(OUT + "descriptive_stats.csv", float_format="%.4f")

# Step 4: the median of each condition in each run separately, to see whether the 5 runs agree.
run_medians = data.groupby(["algorithm", "size", "order", "run"])["us"].median().unstack("run")
run_medians.add_prefix("median_run").to_csv(OUT + "run_medians.csv", float_format="%.4f")

# Step 5: growth factors (for H4): median with 100 numbers / median with 10 numbers, and so on.
medians = stats["median"].unstack("size")  # one row per algorithm and order, one column per size
growth = pd.DataFrame({
    "10->100": medians[100] / medians[10],
    "100->1000": medians[1000] / medians[100],
    "1000->10000": medians[10000] / medians[1000],
})
growth.to_csv(OUT + "growth_factors.csv", float_format="%.1f")

# Step 6: Tables 1-4 of the report (median and range), one table per array size.
lines = []
for number, size in enumerate(SIZES, start=1):
    name, factor = unit(size)
    lines.append(f"**Table {number}: {size:,} numbers (times in {name})**")
    lines.append("")
    lines.append("| Order | Algorithm | Median | Range (min – max) |")
    lines.append("|---|---|---|---|")
    for order in ORDERS:
        for algorithm in ALGORITHMS:
            row = stats.loc[(algorithm, size, order)] * factor
            lines.append(f"| {NAMES[order]} | {NAMES[algorithm]} | {fmt(row['median'])} "
                         f"| {fmt(row['min'])} – {fmt(row['max'])} |")
    lines.append("")
with open(OUT + "median_range_tables.md", "w", encoding="utf-8") as file:
    file.write("\n".join(lines))

# Step 7: bar chart of the medians: one panel per array size, one group of 3 bars per initial order.
plt.rcParams.update({"font.size": 12})
fig, panels = plt.subplots(1, 4, figsize=(16, 4.5))
for panel, size in zip(panels, SIZES):
    name, factor = unit(size)
    for i, algorithm in enumerate(ALGORITHMS):
        heights = [stats.loc[(algorithm, size, order), "median"] * factor for order in ORDERS]
        positions = [o + (i - 1) * 0.27 for o in range(4)]  # 3 bars side by side around each order
        panel.bar(positions, heights, 0.27, color=COLORS[algorithm], label=NAMES[algorithm])
    panel.set_xticks(range(4))
    panel.set_xticklabels([NAMES[order].replace(" ", "\n") for order in ORDERS], fontsize=10)
    panel.set_ylabel(f"Median time ({name})")
    panel.set_title(f"{size:,} numbers")
    panel.yaxis.set_major_formatter("{x:,g}")
    panel.grid(axis="y", alpha=0.3)
handles, labels = panels[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False)
fig.tight_layout(rect=(0, 0, 1, 0.92))
fig.savefig(OUT + "medians_bar_chart.png", dpi=150)

print(f"Analysed {len(data)} measurements of {len(stats)} conditions; results in {OUT}")
