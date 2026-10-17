#!/usr/bin/env python3
"""Turn bench_commits.sh results into the numbers, plot data and figures for the report.

Usage:
    scripts/make_report_assets.py TIMES_CSV [PERF_CSV] [OUT_DIR]

TIMES_CSV is times.csv from a timing sweep, PERF_CSV is perf.csv from a sweep
run with -p (optional), and OUT_DIR defaults to report/. Writes:
    numbers.tex         one LaTeX macro per measured value, used by the report text
    series.csv          cumulative speedup per commit (pgfplots data)
    counters.csv        square-wave time, cycles and instructions relative to -O3
    table_times.tex     median end-to-end seconds per optimization and benchmark
    table_counters.tex  hardware counters for cancer and square-wave
    fig_speedup.pdf     cumulative speedup over the -O0 baseline (log scale)
    fig_counters.pdf    square-wave time, cycles and instructions, indexed to -O3
"""
import csv
import os
import statistics
import sys
from collections import OrderedDict, defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FixedLocator, NullFormatter  # noqa: E402

BENCHES = ["diabetes", "cancer", "housing", "silk-wave", "square-wave"]
BENCH_SHORT = {"diabetes": "diab.", "cancer": "cancer", "housing": "housing",
               "silk-wave": "silk", "square-wave": "square"}

# Short x-axis names for each optimization commit.
SHORT = OrderedDict([
    ("feebc15", "-O0"),
    ("a4d0b6d", "-O3"),
    ("0a0c6d1", "stack"),
    ("de6b4e1", "OpenMP"),
    ("c6b6a9d", "y_pred buf"),
    ("cbba732", "reproduce"),
    ("86dc1ab", "sort"),
    ("ae2edf6", "logLoss"),
    ("2ab2945", "MSE"),
    ("5df15a0", "column"),
    ("4c03341", "pointer"),
])

# Row names for the tables: short enough for one ACM column.
TABLE_LABEL = {
    "feebc15": "Baseline (-O0)",
    "a4d0b6d": "-O3",
    "0a0c6d1": "O(1) stack",
    "de6b4e1": "OpenMP",
    "c6b6a9d": "Reuse y_pred",
    "cbba732": "Skip reproduced",
    "86dc1ab": "Stable sort",
    "ae2edf6": "Par.\\ logLoss",
    "2ab2945": "Par.\\ fused MSE",
    "5df15a0": "Column eval.",
    "4c03341": "Pointer stack",
}


def row_label(commit, labels):
    if commit in TABLE_LABEL:
        return TABLE_LABEL[commit].replace("_", r"\_")
    return tex(labels[commit])


def fmt_seconds(s):
    return f"{s:.0f}" if s >= 100 else f"{s:.1f}" if s >= 10 else f"{s:.2f}"

# Reference categorical palette, fixed order (light mode). Marker shapes and
# line styles carry identity too, for grayscale print and color-vision deficiency.
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
MARKERS = ["o", "s", "^", "D", "v"]
LINESTYLES = ["-", "--", "-.", ":", (0, (5, 1, 1, 1))]
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"


def setup_matplotlib():
    plt.rcParams.update({
        "pdf.fonttype": 42,  # TrueType: ACM rejects Type 3 fonts
        "ps.fonttype": 42,
        "font.size": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.fontsize": 6,
        "axes.edgecolor": INK_SECONDARY,
        "axes.labelcolor": INK,
        "xtick.color": INK_SECONDARY,
        "ytick.color": INK_SECONDARY,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "lines.linewidth": 1.1,
        "lines.markersize": 3.2,
    })


def tex(s):
    return s.replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def load_times(path):
    labels = OrderedDict()
    runs = defaultdict(list)
    matches = []
    for r in csv.DictReader(open(path)):
        labels.setdefault(r["commit"], r["label"])
        runs[(r["commit"], r["benchmark"])].append(float(r["seconds"]))
        matches.append(r["matches_ref"])
    median = {k: statistics.median(v) for k, v in runs.items()}
    return labels, median, matches


def table_times(labels, median, out):
    commits = list(labels)
    base, o3, last = commits[0], commits[1], commits[-1]
    lines = [
        r"\begin{table}[t]",
        r"\centering\footnotesize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\caption{Median end-to-end time (s) after each optimization, cumulative "
        r"(3 runs; the -O0 baseline 1 run). Every run's output is identical to "
        r"the baseline's.}",
        r"\label{tab:times}",
        r"\begin{tabular}{l" + "r" * len(BENCHES) + "}",
        r"\toprule",
        "Optimization & " + " & ".join(BENCH_SHORT[b] for b in BENCHES) + r" \\",
        r"\midrule",
    ]
    for c in commits:
        cells = [fmt_seconds(median[(c, b)]) for b in BENCHES]
        lines.append(f"{row_label(c, labels)} & " + " & ".join(cells) + r" \\")
    lines.append(r"\midrule")
    for name, ref in [("Speedup vs.\\ -O0", base), ("Speedup vs.\\ -O3", o3)]:
        cells = [f"{median[(ref, b)] / median[(last, b)]:.0f}$\\times$" for b in BENCHES]
        lines.append(f"{name} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", ""]
    open(os.path.join(out, "table_times.tex"), "w").write("\n".join(lines))


def load_perf(path):
    rows = OrderedDict()
    for r in csv.DictReader(open(path)):
        rows[(r["commit"], r["benchmark"])] = r
    return rows


def table_counters(perf, labels, out):
    commits = [c for c in labels if any(k[0] == c for k in perf)]
    benches = [b for b in ("cancer", "square-wave") if any(k[1] == b for k in perf)]
    lines = [
        r"\begin{table*}[t]",
        r"\centering\footnotesize",
        r"\setlength{\tabcolsep}{4pt}",
        r"\caption{Hardware counters per optimization (one \texttt{perf stat} run; "
        r"cycles and instructions in billions, summed over all threads). "
        r"Branch-miss \% is misses per branch.}",
        r"\label{tab:counters}",
        r"\begin{tabular}{l" + "rrrrr" * len(benches) + "}",
        r"\toprule",
        " & " + " & ".join(rf"\multicolumn{{5}}{{c}}{{{b}}}" for b in benches) + r" \\",
        " ".join(rf"\cmidrule(lr){{{2 + 5 * i}-{6 + 5 * i}}}" for i in range(len(benches))),
        "Optimization" + " & time (s) & cycles & instr. & IPC & miss\\%" * len(benches) + r" \\",
        r"\midrule",
    ]
    for c in commits:
        cells = []
        for b in benches:
            r = perf.get((c, b))
            if r is None:
                cells += ["--"] * 5
                continue
            cells += [f"{float(r['seconds']):.2f}",
                      f"{int(r['cycles']) / 1e9:.1f}",
                      f"{int(r['instructions']) / 1e9:.1f}",
                      f"{float(r['ipc']):.2f}",
                      f"{float(r['branch_miss_pct']):.3f}"]
        lines.append(f"{row_label(c, labels)} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}", ""]
    open(os.path.join(out, "table_counters.tex"), "w").write("\n".join(lines))


def pow2_axis(ax, lo, hi):
    ticks = [2 ** k for k in range(0, 12) if lo <= 2 ** k <= hi * 1.01]
    ax.set_yscale("log", base=2)
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.set_yticklabels([f"{t:g}$\\times$" for t in ticks])
    ax.yaxis.set_minor_formatter(NullFormatter())


def fig_speedup(labels, median, out):
    commits = list(labels)
    base = commits[0]
    x = list(range(len(commits)))
    fig, ax = plt.subplots(figsize=(3.33, 2.2))
    top = 1
    for i, b in enumerate(BENCHES):
        y = [median[(base, b)] / median[(c, b)] for c in commits]
        top = max(top, max(y))
        ax.plot(x, y, color=COLORS[i], marker=MARKERS[i], linestyle=LINESTYLES[i],
                label=b, clip_on=False, zorder=3)
    pow2_axis(ax, 1, top)
    ax.set_ylim(0.9, top * 1.15)
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT.get(c, c) for c in commits], rotation=45, ha="right",
                       rotation_mode="anchor")
    ax.set_xlim(-0.3, len(commits) - 0.7)
    ax.set_ylabel("Speedup over -O0 baseline")
    ax.legend(loc="lower right", frameon=False, handlelength=2.6, labelcolor=INK)
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(out, "fig_speedup.pdf"))
    plt.close(fig)


def fig_counters(perf, labels, out, bench="square-wave"):
    commits = [c for c in labels if (c, bench) in perf]
    if len(commits) < 2:
        return
    ref = perf[(commits[0], bench)]
    series = [
        ("wall time", "seconds", float),
        ("cycles (all threads)", "cycles", int),
        ("instructions", "instructions", int),
    ]
    x = list(range(len(commits)))
    fig, ax = plt.subplots(figsize=(3.33, 2.2))
    lowest = 1
    for i, (name, key, conv) in enumerate(series):
        y = [conv(perf[(c, bench)][key]) / conv(ref[key]) for c in commits]
        lowest = min(lowest, min(y))
        ax.plot(x, y, color=COLORS[i], marker=MARKERS[i], linestyle=LINESTYLES[i],
                label=name, clip_on=False, zorder=3)
    ticks = [2 ** -k for k in range(0, 8) if 2 ** -k >= lowest * 0.99]
    ax.set_yscale("log", base=2)
    ax.yaxis.set_major_locator(FixedLocator(ticks))
    ax.set_yticklabels(["1" if t == 1 else f"1/{round(1 / t)}" for t in ticks])
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_ylim(lowest / 1.2, 1.12)
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT.get(c, c) for c in commits], rotation=45, ha="right",
                       rotation_mode="anchor")
    ax.set_xlim(-0.3, len(commits) - 0.7)
    ax.set_ylabel(f"{bench}, relative to -O3")
    ax.legend(loc="lower left", frameon=False, handlelength=2.6, labelcolor=INK)
    fig.tight_layout(pad=0.3)
    fig.savefig(os.path.join(out, "fig_counters.pdf"))
    plt.close(fig)


# LaTeX macro names (letters only) for commits and benchmarks, used by numbers.tex.
MACRO_OPT = {
    "feebc15": "Base", "a4d0b6d": "Othree", "0a0c6d1": "Stack", "de6b4e1": "Omp",
    "c6b6a9d": "Ypred", "cbba732": "Repro", "86dc1ab": "Sort", "ae2edf6": "Logloss",
    "2ab2945": "Mse", "5df15a0": "Column", "4c03341": "Pointer",
}
MACRO_BENCH = {"diabetes": "Diab", "cancer": "Cancer", "housing": "Housing",
               "silk-wave": "Silk", "square-wave": "Square"}


def write_numbers(labels, median, perf, out):
    """numbers.tex: one macro per measured value, so the text never hard-codes them.

    \\t<Opt><Bench>     median seconds         \\step<Opt><Bench> speedup over previous step
    \\pct<Opt><Bench>   % time cut vs previous \\cum<Bench>, \\cumOthree<Bench> total speedups
    \\cyc / \\ins / \\br  billions (all threads)  \\ipc, \\miss (% of branches), \\bm (millions)
    """
    commits = [c for c in labels if c in MACRO_OPT]
    lines = ["% Generated by scripts/make_report_assets.py -- do not edit by hand."]

    def define(name, value):
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")

    for b in BENCHES:
        mb = MACRO_BENCH[b]
        prev = None
        for c in commits:
            mo = MACRO_OPT[c]
            define(f"t{mo}{mb}", fmt_seconds(median[(c, b)]))
            if prev is not None:
                ratio = median[(prev, b)] / median[(c, b)]
                define(f"step{mo}{mb}", f"{ratio:.2f}")
                define(f"pct{mo}{mb}", f"{(1 - 1 / ratio) * 100:.0f}")
            prev = c
        define(f"cum{mb}", f"{median[(commits[0], b)] / median[(commits[-1], b)]:.0f}")
        define(f"cumOthree{mb}", f"{median[(commits[1], b)] / median[(commits[-1], b)]:.0f}")

    for (c, b), r in (perf or {}).items():
        if c not in MACRO_OPT or b not in MACRO_BENCH:
            continue
        key = MACRO_OPT[c] + MACRO_BENCH[b]
        define(f"cyc{key}", f"{int(r['cycles']) / 1e9:.0f}")
        define(f"ins{key}", f"{int(r['instructions']) / 1e9:.0f}")
        define(f"br{key}", f"{int(r['branches']) / 1e9:.0f}")
        define(f"bm{key}", f"{int(r['branch_misses']) / 1e6:.0f}")
        define(f"ipc{key}", f"{float(r['ipc']):.2f}")
        define(f"miss{key}", f"{float(r['branch_miss_pct']):.3f}")
    open(os.path.join(out, "numbers.tex"), "w").write("\n".join(lines) + "\n")


def write_plot_tables(labels, median, perf, out):
    """series.csv (cumulative speedup per step) and counters.csv (square-wave,
    indexed to -O3) for pgfplots."""
    commits = list(labels)
    base = commits[0]
    with open(os.path.join(out, "series.csv"), "w") as f:
        f.write("label,diab,cancer,housing,silk,square\n")
        for c in commits:
            vals = [median[(base, b)] / median[(c, b)] for b in BENCHES]
            f.write(SHORT.get(c, c).replace("_", r"\_") + "," +
                    ",".join(f"{v:.3f}" for v in vals) + "\n")
    rows = [c for c in commits if (c, "square-wave") in (perf or {})]
    if rows:
        ref = perf[(rows[0], "square-wave")]
        with open(os.path.join(out, "counters.csv"), "w") as f:
            f.write("label,time,cycles,instr\n")
            for c in rows:
                r = perf[(c, "square-wave")]
                f.write(SHORT.get(c, c).replace("_", r"\_") + "," + ",".join(
                    f"{float(r[k]) / float(ref[k]):.4f}"
                    for k in ("seconds", "cycles", "instructions")) + "\n")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    times = sys.argv[1]
    perf_path = sys.argv[2] if len(sys.argv) > 2 else ""
    out = sys.argv[3] if len(sys.argv) > 3 else "report"
    os.makedirs(out, exist_ok=True)
    setup_matplotlib()

    labels, median, matches = load_times(times)
    bad = [m for m in matches if m != "yes"]
    if bad:
        print(f"warning: {len(bad)} timed runs do not match the reference output")
    table_times(labels, median, out)
    fig_speedup(labels, median, out)

    perf = None
    if os.path.exists(perf_path):
        perf = load_perf(perf_path)
        table_counters(perf, labels, out)
        fig_counters(perf, labels, out)
    write_numbers(labels, median, perf, out)
    write_plot_tables(labels, median, perf, out)
    print(f"wrote {', '.join(sorted(os.listdir(out)))} to {out}/")


if __name__ == "__main__":
    main()
