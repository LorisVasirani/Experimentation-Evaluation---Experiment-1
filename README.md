# Bubble Sort Performance Experiment

I measured the execution time of three bubble sort versions (PassPerItem, UntilNoChange,
WhileNeeded) on arrays of 10, 100, 1,000 and 10,000 numbers in four initial orders
(sorted, reversed, random, almost sorted). Each of the 48 conditions was measured 150 times
(30 measurements × 5 runs) with `System.nanoTime()`.

## Contents

| Path | Content |
|---|---|
| `src/exp01/` | The three algorithms + `Sorter` interface (unmodified) and my measurement program `BubbleBenchmark.java` |
| `run_experiment.sh` | Compiles the code and runs the experiment 5 times |
| `analysis/analyze.py` | Computes the statistics and creates the graph |
| `results/run1.csv` … `run5.csv` | Raw measurements (one row per batch) |
| `results/environment.txt` | Computer and Java details of my run |
| `results/analysis/` | Statistics tables and graph used in the report |

## How to reproduce

Requirements: Java 25 and Python 3.

```bash
./run_experiment.sh                     # about 10 minutes
python3 -m venv .venv
.venv/bin/pip install pandas matplotlib
.venv/bin/python analysis/analyze.py    # writes results/analysis/
```

Before running, close all other applications and connect the computer to the power adapter.
