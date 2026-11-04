#!/usr/bin/env bash
#
# Runs the whole experiment (about 10 minutes): compiles the code and runs the
# measurement program 5 times, each in a new JVM. Output goes to results/.
#
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p results

# Record the machine and JVM used
{
    date
    sw_vers
    sysctl -n machdep.cpu.brand_string hw.ncpu hw.memsize
    pmset -g batt | head -1
    java -version 2>&1
} > results/environment.txt

javac -d out src/exp01/*.java

for run in 1 2 3 4 5; do
    java -Xms2g -Xmx2g -cp out exp01.BubbleBenchmark "$run" > "results/run$run.csv"
done
