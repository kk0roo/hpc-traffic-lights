import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import ensure_dir

PLOT_DIR = os.path.join("results", "plots")


def _load_gen(results_dir, generation):
    agg = os.path.join(results_dir, f"gen_{generation}", "all.csv")
    if os.path.exists(agg):
        df = pd.read_csv(agg)
        if "status" in df.columns:
            df = df[df["status"] == "ok"]
        return df if not df.empty else None
    return None


def plot_convergence(gen_dfs, baseline_val, output_path):
    gens, bests, means, worsts = [], [], [], []
    for i, df in enumerate(gen_dfs):
        if df is None:
            continue
        vals = df["avg_waiting_time"].dropna()
        if vals.empty:
            continue
        gens.append(i)
        bests.append(vals.min())
        means.append(vals.mean())
        worsts.append(vals.max())

    if not gens:
        print("[plot_ea_progress] no data for convergence plot, skipping.")
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(gens, bests, worsts, alpha=0.12, color="#2A6FDB", label="Best-Worst range")
    ax.plot(gens, worsts, ":", color="#2A6FDB", linewidth=0.8)
    ax.plot(gens, means, "o-", color="#2A6FDB", linewidth=2, markersize=5, label="Mean")
    ax.plot(gens, bests, "^-", color="#27AE60", linewidth=2, markersize=6, label="Best")
    if baseline_val is not None:
        ax.axhline(baseline_val, color="#E74C3C", linestyle="--", linewidth=1.5,
                   label=f"Baseline ({baseline_val:.2f} s)")

    ax.set_xlabel("Generation", fontsize=12)
    ax.set_ylabel("Avg Waiting Time [s]", fontsize=12)
    ax.set_title("EA Convergence - Traffic Light Optimisation (3x3 Grid)", fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(gens)
    plt.tight_layout()
    ensure_dir(output_path)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot_ea_progress] wrote {output_path}")


def plot_population_scatter(gen_dfs, output_path):
    valid = [(i, df) for i, df in enumerate(gen_dfs) if df is not None and not df.empty]
    if not valid:
        print("[plot_ea_progress] no data for scatter plot, skipping.")
        return

    n = len(valid)
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows), squeeze=False)

    all_fits = pd.concat([df["avg_waiting_time"].dropna() for _, df in valid])
    vmin, vmax = all_fits.min(), all_fits.max()

    sc_ref = None
    for plot_idx, (gen_idx, df) in enumerate(valid):
        r, c = divmod(plot_idx, cols)
        ax = axes[r][c]
        sc_ref = ax.scatter(
            df["green_ns"], df["green_ew"],
            c=df["avg_waiting_time"],
            cmap="viridis_r", vmin=vmin, vmax=vmax,
            alpha=0.75, s=45, edgecolors="none",
        )
        ax.set_title(f"Generation {gen_idx}", fontsize=11)
        ax.set_xlabel("green_ns [s]", fontsize=9)
        ax.set_ylabel("green_ew [s]", fontsize=9)
        ax.grid(True, alpha=0.25)

    for plot_idx in range(len(valid), rows * cols):
        r, c = divmod(plot_idx, cols)
        axes[r][c].set_visible(False)

    if sc_ref is not None:
        fig.colorbar(sc_ref, ax=axes.ravel().tolist(), label="Avg Waiting Time [s]", shrink=0.6)

    fig.suptitle("Population Evolution: NS vs EW Green Time", fontsize=13, y=1.01)
    plt.tight_layout()
    ensure_dir(output_path)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot_ea_progress] wrote {output_path}")


def plot_comparison(baseline_val, random_val, ea_val, output_path):
    labels = ["Baseline", "Random Best", "EA Best"]
    values = [baseline_val, random_val, ea_val]
    colors = ["#95A5A6", "#3498DB", "#27AE60"]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(labels, values, color=colors, width=0.5, zorder=3)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.15,
            f"{val:.2f} s",
            ha="center", va="bottom", fontsize=11, fontweight="bold",
        )

    if ea_val < baseline_val:
        improvement = 100 * (1 - ea_val / baseline_val)
        ax.annotate(
            f"-{improvement:.1f}%",
            xy=(2, ea_val / 2),
            ha="center", va="center",
            fontsize=12, color="white", fontweight="bold",
        )

    ax.set_ylabel("Avg Waiting Time [s]", fontsize=12)
    ax.set_title("Result Comparison: Baseline vs Random vs EA", fontsize=12)
    ax.set_ylim(0, max(values) * 1.2)
    ax.grid(True, axis="y", alpha=0.3, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    ensure_dir(output_path)
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot_ea_progress] wrote {output_path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate EA progress visualisations.")
    parser.add_argument("--results-dir", default="results", help="Root results directory.")
    parser.add_argument("--generations", type=int, default=6, help="Number of EA generations.")
    parser.add_argument("--baseline", default="results/baseline_metrics.csv",
                        help="Baseline CSV to show as reference line.")
    parser.add_argument("--random-results", default=None,
                        help="Aggregated CSV from random search (for comparison bar).")
    parser.add_argument("--plot-dir", default=PLOT_DIR, help="Output directory for plots.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    ensure_dir(args.plot_dir)

    gen_dfs = [_load_gen(args.results_dir, g) for g in range(args.generations)]

    baseline_val = None
    if os.path.exists(args.baseline):
        bdf = pd.read_csv(args.baseline)
        if not bdf.empty:
            baseline_val = float(bdf["avg_waiting_time"].iloc[0])
            print(f"[plot_ea_progress] baseline avg_waiting_time = {baseline_val:.4f} s")

    plot_convergence(gen_dfs, baseline_val, os.path.join(args.plot_dir, "ea_convergence.png"))
    plot_population_scatter(gen_dfs, os.path.join(args.plot_dir, "ea_population_scatter.png"))

    ea_best = None
    for df in reversed(gen_dfs):
        if df is not None and not df.empty:
            ea_best = float(df["avg_waiting_time"].min())
            break

    random_best = None
    if args.random_results and os.path.exists(args.random_results):
        rdf = pd.read_csv(args.random_results)
        if "status" in rdf.columns:
            rdf = rdf[rdf["status"] == "ok"]
        if not rdf.empty:
            random_best = float(rdf["avg_waiting_time"].min())

    if baseline_val is not None and ea_best is not None:
        rb = random_best if random_best is not None else baseline_val
        plot_comparison(
            baseline_val, rb, ea_best,
            os.path.join(args.plot_dir, "ea_final_comparison.png"),
        )
    else:
        print("[plot_ea_progress] skipping comparison chart (missing baseline or EA results).")


if __name__ == "__main__":
    main()
