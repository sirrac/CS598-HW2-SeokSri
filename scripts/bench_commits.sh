#!/usr/bin/env bash
# Benchmark each optimization commit end to end.
#
# For every commit: build it in a temporary git worktree (the working tree is
# never touched), run each benchmark N times, record the end-to-end time that
# genetic_benchmark prints, and check that the program output (minus timing
# lines) is identical to the reference commit's output.
#
# Usage:
#   scripts/bench_commits.sh                  # full sweep, all commits and benchmarks
#   scripts/bench_commits.sh [-r RUNS] [-B BASE_RUNS] [-b "BENCHES"]
#                            [-c "COMMITS"] [-R REF_COMMIT] [-o OUT_DIR] [-p]
#
#   -r RUNS        runs per (commit, benchmark)          default: 3
#   -B BASE_RUNS   runs for the reference commit          default: 1 (it is slow)
#   -b BENCHES     space-separated benchmark names       default: all five
#   -c COMMITS     space-separated commits, in order     default: optimization history
#   -R REF_COMMIT  commit whose output is the reference  default: feebc15 (baseline)
#   -o OUT_DIR     where results are written             default: bench_results/<timestamp>
#   -p             also collect hardware counters: one extra run per
#                  (commit, benchmark) under `perf stat`, separate from the
#                  timed runs. Skipped with a warning if perf is unavailable.
#                  e.g. scripts/bench_commits.sh -p -b "cancer square-wave"
#
# The reference commit always runs first, so every other commit's output can be
# checked against it.
#
# Results (bench_results/latest points to the most recent sweep):
#   OUT_DIR/times.csv             commit,label,benchmark,run,seconds,matches_ref
#   OUT_DIR/perf.csv              (with -p) commit,label,benchmark,seconds,cycles,
#                                 instructions,branches,branch_misses,ipc,
#                                 branch_miss_pct  (counts summed over all threads)
#   OUT_DIR/outputs/<commit>/     first-run output of each benchmark
#   OUT_DIR/machine.txt           CPU, core count, compiler, date
#
# Passing an existing -o OUT_DIR appends to its times.csv, so a sweep can be
# split across invocations and still be checked against the saved reference.
#
# Note: the -O0 baseline is slow (README reference: silk-wave ~226 s,
# square-wave ~714 s per run), and a full sweep takes about an hour. Run it
# under tmux or nohup, on an otherwise idle machine.

set -euo pipefail

RUNS=3
BASE_RUNS=1
BENCHES="diabetes cancer housing silk-wave square-wave"
COMMITS=""
REF=feebc15
OUT_DIR=""
PERF=0
PERF_EVENTS="cycles,instructions,branches,branch-misses"

# Default commit sequence with short labels for plots.
DEFAULT_COMMITS=(
  "feebc15:baseline (-O0)"
  "a4d0b6d:-O3"
  "0a0c6d1:O(1) stack push/pop"
  "de6b4e1:OpenMP over programs"
  "c6b6a9d:reuse y_pred buffer"
  "cbba732:skip reproduced programs"
  "86dc1ab:stable index sort + move ops"
  "ae2edf6:parallel logLoss"
  "2ab2945:parallel + fused MSE"
  "5df15a0:column-wise node evaluation"
  "4c03341:push variable columns by pointer"
)

while getopts "r:B:b:c:R:o:ph" opt; do
  case $opt in
    p) PERF=1 ;;
    r) RUNS=$OPTARG ;;
    B) BASE_RUNS=$OPTARG ;;
    b) BENCHES=$OPTARG ;;
    c) COMMITS=$OPTARG ;;
    R) REF=$OPTARG ;;
    o) OUT_DIR=$OPTARG ;;
    h) sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) exit 1 ;;
  esac
done

REPO=$(git rev-parse --show-toplevel)
cd "$REPO"
if [[ -z "$OUT_DIR" ]]; then
  OUT_DIR="bench_results/$(date +%Y%m%d-%H%M%S)"
  mkdir -p bench_results
  ln -sfn "$(basename "$OUT_DIR")" bench_results/latest
fi
mkdir -p "$OUT_DIR/outputs"
OUT_DIR=$(cd "$OUT_DIR" && pwd)
CSV="$OUT_DIR/times.csv"
REF=$(git rev-parse --short "$REF")
echo "Results: $OUT_DIR"

# Build the (commit, label) list.
declare -a ENTRIES=()
if [[ -z "$COMMITS" ]]; then
  ENTRIES=("${DEFAULT_COMMITS[@]}")
else
  for c in $COMMITS; do
    label=""
    for e in "${DEFAULT_COMMITS[@]}"; do
      [[ "$(git rev-parse --short "${e%%:*}")" == "$(git rev-parse --short "$c")" ]] && label=${e#*:}
    done
    [[ -z "$label" ]] && label=$(git log -1 --format=%s "$c")
    ENTRIES+=("$c:$label")
  done
fi

# Run the reference commit first so the others can be checked against it.
declare -a ORDERED=()
for e in "${ENTRIES[@]}"; do
  [[ "$(git rev-parse --short "${e%%:*}")" == "$REF" ]] && ORDERED+=("$e")
done
for e in "${ENTRIES[@]}"; do
  [[ "$(git rev-parse --short "${e%%:*}")" != "$REF" ]] && ORDERED+=("$e")
done
ENTRIES=("${ORDERED[@]}")

{
  echo "date: $(date -Is)"
  echo "host: $(hostname)"
  echo "nproc: $(nproc)"
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ //')"
  echo "compiler: $(g++ --version | head -1)"
  echo "OMP_NUM_THREADS: ${OMP_NUM_THREADS:-unset (all cores)}"
} > "$OUT_DIR/machine.txt"

[[ -f "$CSV" ]] || echo "commit,label,benchmark,run,seconds,matches_ref" > "$CSV"

# Sums one event from `perf stat -x,` output. Handles PMU-prefixed names
# (e.g. cpu_core/cycles/ on hybrid CPUs) and skips <not counted> values.
perf_event() {
  awk -F, -v ev="$1" '{
    e = $3; sub(/:.*$/, "", e); sub(/\/$/, "", e); sub(/^.*\//, "", e)
    if (e == ev && $1 ~ /^[0-9]+$/) { s += $1; found = 1 }
  } END { if (found) printf "%d", s }' "$2"
}

PCSV="$OUT_DIR/perf.csv"
if [[ $PERF -eq 1 ]]; then
  probe=$(mktemp)
  if command -v perf >/dev/null 2>&1 &&
     perf stat -x, -e cycles -o "$probe" true >/dev/null 2>&1 &&
     [[ -n "$(perf_event cycles "$probe")" ]]; then
    [[ -f "$PCSV" ]] || echo "commit,label,benchmark,seconds,cycles,instructions,branches,branch_misses,ipc,branch_miss_pct" > "$PCSV"
  else
    echo "warning: perf stat is unavailable or cannot read hardware counters;" \
         "skipping -p (timed runs are unaffected)" >&2
    PERF=0
  fi
  rm -f "$probe"
fi

WORK=$(mktemp -d)
cleanup() {
  for wt in "$WORK"/*; do
    [[ -d "$wt" ]] && git -C "$REPO" worktree remove --force "$wt" 2>/dev/null || true
  done
  git -C "$REPO" worktree prune
  rm -rf "$WORK"
}
trap cleanup EXIT

strip_timing() { grep -v ';;Time(' "$1"; }

for entry in "${ENTRIES[@]}"; do
  commit=$(git rev-parse --short "${entry%%:*}")
  label=${entry#*:}
  wt="$WORK/$commit"

  echo "== $commit  $label"
  git worktree add -q --detach "$wt" "$commit"
  if ! make -C "$wt" -j"$(nproc)" >"$WORK/$commit.build.log" 2>&1; then
    echo "   build failed, see $WORK/$commit.build.log" >&2
    continue
  fi

  runs=$RUNS
  [[ "$commit" == "$REF" ]] && runs=$BASE_RUNS

  mkdir -p "$OUT_DIR/outputs/$commit"
  for bench in $BENCHES; do
    for run in $(seq 1 "$runs"); do
      out="$WORK/$commit.$bench.$run.txt"
      (cd "$wt" && ./genetic_benchmark "$bench" >"$out" 2>&1)
      secs=$(awk '/;;Time\(/ {print $(NF-1)}' "$out")

      if [[ $run -eq 1 ]]; then
        cp "$out" "$OUT_DIR/outputs/$commit/$bench.txt"
      fi
      ref_out="$OUT_DIR/outputs/$REF/$bench.txt"
      if [[ -f "$ref_out" ]]; then
        if diff -q <(strip_timing "$ref_out") <(strip_timing "$out") >/dev/null; then
          match=yes
        else
          match=NO
        fi
      else
        match=n/a
      fi

      printf '%s,"%s",%s,%s,%s,%s\n' "$commit" "$label" "$bench" "$run" "$secs" "$match" >> "$CSV"
      printf '   %-12s run %s: %8s s  output matches %s: %s\n' "$bench" "$run" "$secs" "$REF" "$match"
    done

    # One extra run under perf stat, kept out of the timed runs above.
    if [[ $PERF -eq 1 ]]; then
      pout="$WORK/$commit.$bench.perf.txt"
      pstat="$WORK/$commit.$bench.perfstat"
      (cd "$wt" && perf stat -x, -e "$PERF_EVENTS" -o "$pstat" \
        ./genetic_benchmark "$bench" >"$pout" 2>&1)
      psecs=$(awk '/;;Time\(/ {print $(NF-1)}' "$pout")
      cyc=$(perf_event cycles "$pstat")
      ins=$(perf_event instructions "$pstat")
      br=$(perf_event branches "$pstat")
      bm=$(perf_event branch-misses "$pstat")
      ipc=$(awk -v i="$ins" -v c="$cyc" 'BEGIN { if (c > 0 && i != "") printf "%.3f", i / c }')
      bmp=$(awk -v m="$bm" -v b="$br" 'BEGIN { if (b > 0 && m != "") printf "%.3f", 100 * m / b }')
      printf '%s,"%s",%s,%s,%s,%s,%s,%s,%s,%s\n' "$commit" "$label" "$bench" "$psecs" \
        "$cyc" "$ins" "$br" "$bm" "$ipc" "$bmp" >> "$PCSV"
      printf '   %-12s perf : IPC %s, branch misses %s%%\n' "$bench" "${ipc:-n/a}" "${bmp:-n/a}"
    fi
  done
  git worktree remove --force "$wt"
done

# Summary: median seconds per (commit, benchmark), in the order of times.csv.
echo
echo "Median seconds (from $CSV):"
awk -F, 'NR > 1 {
  key = $1 FS $3
  if (!(key in n)) order[++k] = key
  v[key, ++n[key]] = $(NF-1)
  lab[$1] = $2; gsub(/"/, "", lab[$1])
}
END {
  for (i = 1; i <= k; i++) {
    key = order[i]; m = n[key]
    for (a = 1; a <= m; a++) s[a] = v[key, a] + 0
    for (a = 1; a <= m; a++) for (b = a + 1; b <= m; b++) if (s[b] < s[a]) { t = s[a]; s[a] = s[b]; s[b] = t }
    med = (m % 2) ? s[(m + 1) / 2] : (s[m / 2] + s[m / 2 + 1]) / 2
    split(key, p, FS)
    printf "  %-9s %-34s %-12s %10.3f\n", p[1], lab[p[1]], p[2], med
  }
}' "$CSV"

if [[ -f "$PCSV" ]]; then
  echo
  echo "Hardware counters (from $PCSV, summed over threads):"
  printf "  %-9s %-12s %10s %16s %16s %6s %8s\n" commit benchmark seconds cycles instructions IPC "miss%"
  awk -F, 'NR > 1 { printf "  %-9s %-12s %10.3f %16s %16s %6s %8s\n", $1, $3, $4, $5, $6, $9, $10 }' "$PCSV"
fi
