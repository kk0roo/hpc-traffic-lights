import argparse
import math
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd


def _load_task_runtimes(results_dir, prefix, worker_counts):
    """Return {N: [per-task runtime_seconds, ...]} for each available level."""
    data = {}
    for n in worker_counts:
        d = os.path.join(results_dir, f"{prefix}_n{n}")
        if not os.path.isdir(d):
            continue
        csvs = [os.path.join(d, f) for f in os.listdir(d)
                if f.endswith(".csv") and not f.startswith("slurm")]
        if not csvs:
            continue
        frames = []
        for p in csvs:
            try:
                frames.append(pd.read_csv(p))
            except Exception:
                pass
        if not frames:
            continue
        df = pd.concat(frames, ignore_index=True)
        if "runtime_seconds" in df.columns:
            runtimes = df["runtime_seconds"].dropna().tolist()
            if runtimes:
                data[n] = runtimes
    return data


def _greedy_makespan(times, n_workers):
    """Wall time to run `times` (per-task seconds) on n_workers (LPT schedule)."""
    if n_workers <= 1:
        return sum(times)
    loads = [0.0] * n_workers
    for t in sorted(times, reverse=True):
        i = min(range(n_workers), key=lambda k: loads[k])
        loads[i] += t
    return max(loads)


def plot_scaling(results_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    strong_ns = [1, 2, 5, 10, 20, 50, 100]

    runtimes = _load_task_runtimes(results_dir, "strong", strong_ns)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Strong-scaling analysis (modelled wall time from measured "
                 "per-task runtimes)", fontsize=13, fontweight="bold")

    if runtimes:
        ns = sorted(runtimes)
        # Sequential baseline: total work = sum of all per-task runtimes.
        t1 = sum(runtimes[ns[0]])
        wall = {n: _greedy_makespan(runtimes[n], n) for n in ns}
        speedups = [t1 / wall[n] for n in ns]
        effs = [s / n * 100 for s, n in zip(speedups, ns)]

        ax = axes[0]
        ax.plot(ns, speedups, "o-", label="Measured (makespan model)")
        ax.plot(ns, ns, "--", color="gray", label="Ideal (linear)")
        ax.set_xlabel("Number of workers N")
        ax.set_ylabel("Speedup S(N)")
        ax.set_title("Speedup")
        ax.legend()
        ax.grid(True, alpha=0.3)

        ax = axes[1]
        ax.plot(ns, effs, "s-", color="tab:orange", label="Measured")
        ax.axhline(100, linestyle="--", color="gray", label="Ideal (100%)")
        ax.set_xlabel("Number of workers N")
        ax.set_ylabel("Efficiency E(N) [%]")
        ax.set_title("Parallel efficiency")
        ax.set_ylim(0, 110)
        ax.legend()
        ax.grid(True, alpha=0.3)
    else:
        for ax in axes:
            ax.text(0.5, 0.5, "No data (strong_n*/)", ha="center", va="center",
                    transform=ax.transAxes, color="gray")

    plt.tight_layout()
    out = os.path.join(output_dir, "scaling.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot_scaling] saved {out}")


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/scaling",
                   help="Dir containing strong_n*/ subdirs.")
    p.add_argument("--output-dir", default="results/plots", help="Where to save PNG.")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    plot_scaling(args.results_dir, args.output_dir)


if __name__ == "__main__":
    main()
