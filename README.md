# 598APE-HW2

This repository contains code for homework 2 of 598APE.

In particular, this repository is an implementation of Symbolic Regression and the various contexts it can be used in.

Starting from the course baseline, we applied 10 optimizations (compiler
optimization, an O(1) evaluation stack, OpenMP parallelism, removal of
serial overhead, and a column-wise interpreter) that leave every benchmark's
output identical to the baseline while running the five benchmarks
69-181x faster than the `-O0` baseline and 17-36x faster than `-O3` alone,
on the 4-core course VM. See
[Reproducing Benchmark and Verifying the Optimizations](#reproducing-benchmark-and-verifying-the-optimizations).

To compile the program run:
```bash
make -j
```

To clean existing build artifacts run:
```bash
make clean
```

This program assumes the following are installed on your machine:
* A working C++ compiler (g++ is assumed in the Makefile)
* make
* racket (to plot images)

Running make builds a sample benchmarking binary(`genetic_benchmark`) which you will use for perf engineering. However, note that the symbolic regression routines exposed in `genetic.h` are general, and can be used as a sub-routine in any data science pipeline (pending a Cython wrapper to Python/Torch).

Once compiled, one can run the benchmark code on the diabetes dataset as follows. The output is a valid racket program, which provides the 2 best programs as callable functions - symbolic regression is used for synthesizing these functions. 

```bash
./genetic_benchmark diabetes
#lang racket

;;===== Symbolic Regression Benchmark =====

(provide best-program-1 best-program-2)
;;Loading dataset...
;;Dataset dimensions: 442 samples x 10 features
;;Training symbolic regressor with 512 population size and 16 generations
;;Best program 1 details:
;;- Length: 91 nodes
;;- Depth: 12
;;- Raw fitness: 6302.75
;;- Test MSE: 7468.95
(define best-program-1 (lambda (X)
  (define (div a b) (if (< (abs b) 0.001) 1.0 (/ a b)))
  (define (fdim a b) (max (- a b) 0.0))
  (define (gt a b) (if (> a b) 1.0 0.0))
  (define (acosh a)
    (log (+ a (* (sqrt (- a 1.0)) (sqrt (+ a 1.0))))))
  (define (asinh a)
    (let* ([v (abs a)] [r (log (+ v (sqrt (+ (* v v) 1.0))))])
      (if (< a 0.0) (- r) r)))
  (define (atanh a) (* 0.5 (log (/ (+ 1.0 a) (- 1.0 a)))))
  (define (cbrt a)
    (let ([r (expt (abs a) (/ 1.0 3.0))])
      (if (< a 0.0) (- r) r)))
  (define (cube a) (* a a a))
  (define (inv a) (if (< (abs a) 0.001) 0.0 (/ 1.0 a)))
  (define (rcbrt a) (/ 1.0 (cbrt a)))
  (define (rsqrt a) (/ 1.0 (sqrt (abs a))))
  (define (gp-log a) (if (< (abs a) 0.001) 0.0 (log (abs a))))
  (define (gp-sqrt a) (sqrt (abs a)))
  (*  (-  (-  (+  (cos  (+  (cos  (-  (gp-log  (-  (list-ref X 0) (abs  (list-ref X 8)) ) )  (-  (-  (list-ref X 1) (list-ref X 8))  (sin  (list-ref X 7)) ) ) )  (sin  (cos  (cos  (*  (sin  (cos  (list-ref X 8)) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) ) ) ) ) )  (cos  (*  (list-ref X 7) (list-ref X 7)) ) )  (*  (sin  (cos  (list-ref X 8)) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) )  (-  (-  (cos  (fdim  (list-ref X 2) (list-ref X 9)) )  (-  (cos  (fdim  (list-ref X 8) (list-ref X 6)) )  (gp-log  (list-ref X 0)) ) )  (*  -0.960798442 (list-ref X 5)) ) )  (+  (fdim  (-  (sin  (cos  (+  (list-ref X 5) (list-ref X 0)) ) )  (cos  (cos  (list-ref X 4)) ) )  (+  (gp-log  (list-ref X 1))  (cos  (gp-log  (list-ref X 9)) ) ) )  (+  (-  (fdim  (abs  (list-ref X 3))  (gp-log  (*  (list-ref X 1) (list-ref X 1)) ) )  (gp-log  (*  (list-ref X 1) (list-ref X 1)) ) )  (abs  (cos  (list-ref X 6)) ) ) ) ) ))
;;Best program 2 details:
;;- Length: 199 nodes
;;- Depth: 18
;;- Raw fitness: 6408.27
;;- Test MSE: 7217.17
(define best-program-2 (lambda (X)
  (define (div a b) (if (< (abs b) 0.001) 1.0 (/ a b)))
  (define (fdim a b) (max (- a b) 0.0))
  (define (gt a b) (if (> a b) 1.0 0.0))
  (define (acosh a)
    (log (+ a (* (sqrt (- a 1.0)) (sqrt (+ a 1.0))))))
  (define (asinh a)
    (let* ([v (abs a)] [r (log (+ v (sqrt (+ (* v v) 1.0))))])
      (if (< a 0.0) (- r) r)))
  (define (atanh a) (* 0.5 (log (/ (+ 1.0 a) (- 1.0 a)))))
  (define (cbrt a)
    (let ([r (expt (abs a) (/ 1.0 3.0))])
      (if (< a 0.0) (- r) r)))
  (define (cube a) (* a a a))
  (define (inv a) (if (< (abs a) 0.001) 0.0 (/ 1.0 a)))
  (define (rcbrt a) (/ 1.0 (cbrt a)))
  (define (rsqrt a) (/ 1.0 (sqrt (abs a))))
  (define (gp-log a) (if (< (abs a) 0.001) 0.0 (log (abs a))))
  (define (gp-sqrt a) (sqrt (abs a)))
  (*  (-  (-  (+  (cos  (*  (list-ref X 7) (list-ref X 7)) )  (cos  (*  (list-ref X 7) (list-ref X 7)) ) )  (*  (sin  (cos  (list-ref X 8)) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) )  (-  (-  (gp-log  (list-ref X 6))  (-  (sin  (list-ref X 5))  (gp-log  (list-ref X 0)) ) )  (sin  (sin  (+  (-  (-  (-  (+  (+  (cos  (list-ref X 6))  (fdim  (list-ref X 4) (list-ref X 0)) )  (abs  (gp-log  (list-ref X 3)) ) )  (*  (gp-log  (+  (list-ref X 4) (list-ref X 8)) )  (cos  (sin  (fdim  (-  (list-ref X 0) (list-ref X 9))  (abs  (list-ref X 8)) ) ) ) ) )  (-  (-  (cos  (fdim  (list-ref X 2) (list-ref X 9)) )  (-  (*  (gp-log  (*  (*  (abs  (-  (abs  (list-ref X 8))  (+  (list-ref X 5) (list-ref X 5)) ) )  (sin  (list-ref X 1)) )  (cos  (sin  (list-ref X 1)) ) ) )  (-  (+  (cos  (cos  (list-ref X 0)) )  (+  (fdim  (list-ref X 2) (list-ref X 9))  (abs  (list-ref X 1)) ) )  (cos  (cos  (gp-log  (abs  (-  (list-ref X 5) (list-ref X 7)) ) ) ) ) ) )  (-  (sin  (list-ref X 5))  (gp-log  (list-ref X 0)) ) ) )  (abs  (+  (list-ref X 2) (list-ref X 9)) ) ) )  (abs  (-  (list-ref X 6) (gp-log  (list-ref X 7)) ) ) )  (list-ref X 9)) ) ) ) )  (+  (fdim  (-  (sin  (-  (-  (+  (cos  (+  (cos  (-  (gp-log  (-  (list-ref X 0) (abs  (list-ref X 8)) ) )  (-  (-  (list-ref X 1) (list-ref X 8))  (sin  (list-ref X 7)) ) ) )  (sin  (cos  (cos  (sin  (list-ref X 5)) ) ) ) ) )  (cos  (*  (list-ref X 7) (list-ref X 7)) ) )  (*  (sin  (cos  (list-ref X 8)) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) )  (-  (-  (cos  (fdim  (list-ref X 2) (list-ref X 9)) )  (-  (cos  (fdim  (list-ref X 8) (list-ref X 6)) )  (gp-log  (list-ref X 0)) ) )  (*  -0.960798442 (list-ref X 5)) ) ) )  (cos  (+  (+  (cos  (list-ref X 6))  (list-ref X 9))  (abs  (gp-log  (list-ref X 3)) ) ) ) )  (+  (gp-log  (list-ref X 1))  (cos  (gp-log  (list-ref X 9)) ) ) )  (fdim  (+  (+  (cos  (list-ref X 6))  (*  (list-ref X 7) (list-ref X 7)) )  (abs  (gp-log  (list-ref X 3)) ) )  (gp-log  (-  (list-ref X 6) (list-ref X 5)) ) ) ) ) ))
;;Time(Symbolic Regression (End-to-End)) = 11.512300000 sec

```

`(list-ref X i)` corresponds to the `i`th feature of your dataset (it is Racket syntax to access `X[i]`)

While currently hardcoded to only handle the 3 CSV datasets and 2 image reconstruction tasks, `genetic_benchmark.cpp` in the `benchmarks` folder exposes training code for end to end symbolic regression/binary classification, starting from converting the input data to a columnar format, before dispatching it to `genetic::symFit`. 

The behaviour of the training run can be tuned through the `param` struct, which controls paramenters like the population size, functions being considered, subtree depth and so on.  

```bash
./genetic_benchmark diabetes
```

There are also 2 image reconstruction tasks. The goal of image re-construction is to infer the underlying semantic meaning present in an image. We do this by representing every image as the average of `K` mathematical equations, and output the equations as a valid racket program (which you can also use to draw the final image). All input images have 256x256 pixels, and each pixel stores a r,g,b tuple corresponding to red, green and blue pixel values. For example, on the silk-wave input:

![Silk wave](./benchmark/silk-waves.png)

We now run symbolic regression based reconstruction on the silk-wave picture. 

```bash
./genetic_benchmark silk-wave > silk-ref.rkt
racket silk-ref.rkt silk-waves-reconstructed.png
```

This produces 2 artifacts. [silk-ref.rkt](./benchmark/silk-ref.rkt) contains the symbolic definition of the image. The reconstructed image is 

![Reconstructed Silk wave](./benchmark/silk-waves-reconstructed.png)

Similarly, for the harder square wave benchmark, we start from 

![Square wave](./benchmark/squared-waves.png)

and are able to reconstruct 

![Reconstructed square wave](./benchmark/square-wave-reconstructed.png)

with the source code for the reconstructed wave in [square-wave-ref.rkt](./benchmark/square-wave-ref.rkt)

The time taken for the end to end run can be seen in the last comment of the generated rkt file. Similar to HW1, your goal is to reduce this runtime as much as possible, while maintining/increasing complexity. For the image code, it is sufficient to just optimize image generation, however, you are also free to optimize image drawing too (which is currently implemnented as a DSL in Racket)

## Reproducing Benchmark and Verifying the Optimizations

### Performance (the numbers in the report)

`scripts/bench_commits.sh` reproduces every timing in the report. For each
optimization commit it builds a clean copy in a temporary git worktree, runs all five benchmarks, and records the
end-to-end time that `genetic_benchmark` prints.

```bash
scripts/bench_commits.sh 2>&1 | tee bench.log     # full sweep, ~1 h on 4 cores
scripts/bench_commits.sh -r 1 -b "diabetes cancer housing"   # quick check, no images
scripts/bench_commits.sh -h                       # all options
```

By default the `-O0` baseline runs once and every other commit 3
times. Results go to `bench_results/` (each run replaces the previous
results there; use `-o DIR` to write somewhere else):

- `times.csv`: `commit, label, benchmark, run, seconds, matches_ref`
- `machine.txt`: CPU, core count, compiler
- `outputs/<commit>/`: each commit's benchmark output

**Hardware counters.** With `-p`, the script adds one separate `perf stat` run
per commit and benchmark (cycles, instructions, branches, branch misses) and
writes `perf.csv`. The counter table in the report used the command below,
which writes to its own folder so it does not replace the timing results:

```bash
sudo sysctl kernel.perf_event_paranoid=1     # allow perf to count (resets on reboot)
scripts/bench_commits.sh -p -r 1 -b "cancer square-wave" -R a4d0b6d \
  -c "a4d0b6d 0a0c6d1 de6b4e1 c6b6a9d cbba732 86dc1ab ae2edf6 2ab2945 5df15a0 4c03341" \
  -o bench_results/counters
```

**Report tables and figures.** `scripts/make_report_assets.py` turns
`times.csv` and `perf.csv` into the numbers and plot data used by the report:

```bash
python3 scripts/make_report_assets.py bench_results/times.csv bench_results/counters/perf.csv report
```

### Correctness (identical output)

`bench_commits.sh` compares each run's full output (every evolved program and
its fitness; only the timing line is ignored) against the baseline
(`feebc15`) and records the result in the `matches_ref` column. Every run of
every commit must say `yes`:

```bash
grep -c ',NO$' bench_results/times.csv     # prints 0
```

All 10 shipped commits produce output identical to the baseline on all five
benchmarks.

## Optimizations and How to Evaluate Individually

Each optimization is a single commit on top of the baseline. To measure one in
isolation, time the commit against its parent:

```bash
scripts/bench_commits.sh -c "<commit>~1 <commit>" -R <commit>~1
```

or by hand:

```bash
git checkout <commit>~1 && make clean && make -j    # just before it
git checkout <commit>   && make clean && make -j    # with it
./genetic_benchmark <dataset>                        # e.g. cancer, silk-wave
```

| # | Commit | Kind | Optimization |
|---|---|---|---|
| 0 | `feebc15` | | Baseline (`-O0`, single-threaded) |
| 1 | `a4d0b6d` | compiler | Build at `-O3` instead of `-O0` |
| 2 | `0a0c6d1` | data structure | Evaluation stack: O(1) `push`/`pop` instead of scanning all 20 slots |
| 3 | `de6b4e1` | parallelism | OpenMP `parallel for` over programs in `execute_kernel` |
| 4 | `c6b6a9d` | memory management | Reuse a per-thread prediction buffer instead of allocating it every generation |
| 5 | `cbba732` | work reduction | Skip re-evaluating reproduced programs (their fitness is copied from the parent) |
| 6 | `86dc1ab` | algorithmic | Stable index sort instead of insertion sort with deep copies; move operations for `program` |
| 7 | `ae2edf6` | parallelism | Parallelize `logLoss` over programs |
| 8 | `2ab2945` | parallelism, work reduction | Parallelize `meanSquareError` and fuse its two passes |
| 9 | `5df15a0` | algorithmic | Column-wise interpreter: evaluate node by node over all rows (`evaluate_node_column`) |
| 10 | `4c03341` | copy reduction | Push variable columns onto the stack by pointer instead of copying |

## Input Datasets and Images
This project contains 3 input datasets and 2 images for you to optimize. All 3 are standard scikit-learn datasets. The images are generated bitmaps from `benchmark/generate-easy-image.rkt`.

### Diabetes

```bash
./genetic_benchmark diabetes
```

### Cancer

```bash
./genetic_benchmark cancer
```

### California Housing Prices

```bash
./genetic_benchmark housing
```

### Silk waves

```bash
./genetic_benchmark silk-wave > silk.rkt
racket silk.rkt silk.png
```

### Square waves

```bash
./genetic_benchmark square-wave > square.rkt
racket square.rkt square.png
```

## Code Overview

There are multiple core functions

`cpp_evolve`

`cpp_evolve` is the central evolution driver. It takes a population of candidate programs and produces a new generation by first selecting parents through tournament selection and then applying various mutation strategies (crossover, subtree mutation, hoist mutation, and point mutation) or direct reproduction. After mutation, it updates the fitness of the new generation.

`build_program`

`build_program` constructs an initial candidate program (represented as a syntax tree) using a randomized process. It chooses function nodes and terminal nodes based on specified initialization methods (grow, full, or half-and-half) and ensures that the generated program adheres to a maximum depth constraint.

`tournament_kernel` 

`tournament_kernel` implements the tournament selection process. It randomly samples subsets of the population, evaluates their fitness (including a parsimony penalty for program length), and selects the best candidates to serve as parents for the next generation.

`execute_kernel`

Given a bunch of programs(symbolic formulae), `execute_kernel` evaluates those formulae on the given input dataset and outputs predicted values. We evaluate all programs on all dataset rows. 

`compute_metric`

As the name suggests, we compute the loss/accuracy values according to the metric specified in `params`. There are 5 different metrics supported - logLoss (for classification), mean square error and root mean square error(for regression) and correlation coefficients for transformation (both Karl Pearson and Spearman's rank correlation are implemented). 

## Docker

For ease of use and installation, we provide a docker image capable of running and building code here. The source docker file is in /docker (which is essentially a list of commands to build an OS state from scratch). It contains the dependent compilers, and some other nice things.

Run the docker build for the first time to setup all the environments you need
```bash
./dockerbuild.sh
```

If you now run `./dockerrun.sh` you will enter an interactive bash session with all the packages from docker installed (that script by default uses `vim/598ape`, feel free to replace it with whatever location you like if you built from scratch). The current directory (aka this folder) is mounted within `/host`. Any files you create on your personal machine will be available there, and anything you make in the container in that folder will be available on your personal machine.
