import argparse
import math
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def _load_mc_results(results_dir):
    csvs = sorted(
        os.path.join(results_dir, f)
        for f in os.listdir(results_dir)
        if f.endswith(".csv")
    )
    frames = []
    for p in csvs:
        try:
            frames.append(pd.read_csv(p))
        except Exception:
            pass
    if not frames:
        return None
    df = pd.concat(frames, ignore_index=True)
    if "backend" in df.columns:
        df = df[df["backend"] == "mc"]
    return df


def plot_mc_convergence(results_dir, output_dir, ea_results_dir=None):
    os.makedirs(output_dir, exist_ok=True)

    df = _load_mc_results(results_dir)
    if df is None or df.empty:
        print("[plot_mc_convergence] Brak danych MC.")
        return

    estimates = df["avg_queue_length"].dropna().values
    errors = df["avg_waiting_time"].dropna().values

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Monte Carlo — estymacja π", fontsize=13, fontweight="bold")

    ax = axes[0]
    ns = np.arange(1, len(estimates) + 1)
    running_mean = np.cumsum(estimates) / ns
    ax.plot(ns, running_mean, label="Running mean π")
    ax.axhline(math.pi, color="red", linestyle="--", label=f"Prawdziwe π ≈ {math.pi:.5f}")
    ax.fill_between(ns,
                    running_mean - 2 / np.sqrt(ns),
                    running_mean + 2 / np.sqrt(ns),
                    alpha=0.15, label="95% CI (teoret.)")
    ax.set_xlabel("Liczba zadań (N)")
    ax.set_ylabel("Szacowane π")
    ax.set_title("Konwergencja do π")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    running_err = np.abs(running_mean - math.pi)
    theory_err = 1.0 / np.sqrt(ns)
    ax.loglog(ns, running_err, label="|błąd|")
    ax.loglog(ns, theory_err, "--", color="gray", label="Teoria: 1/√N")
    ax.set_xlabel("Liczba zadań (N)")
    ax.set_ylabel("|π_estym - π|")
    ax.set_title("Błąd estymacji (log-log)")
    ax.legend()
    ax.grid(True, which="both", alpha=0.3)

    ax = axes[2]
    mc_runtimes = df["runtime_seconds"].dropna().values if "runtime_seconds" in df.columns else None

    if mc_runtimes is not None and len(mc_runtimes) > 0:
        total_mc = mc_runtimes.sum()
        mc_ns = np.arange(1, len(mc_runtimes) + 1)
        mc_t1 = mc_runtimes[0] if mc_runtimes[0] > 0 else mc_runtimes.mean()
        mc_speedups = mc_t1 * mc_ns / np.maximum(np.maximum.accumulate(mc_runtimes), 1e-9)
        ax.plot(mc_ns, mc_ns, "--", color="gray", label="Idealne (liniowe)")
        ax.plot(mc_ns, mc_speedups, label="MC (empiryczne)")

    if ea_results_dir and os.path.isdir(ea_results_dir):
        ea_speedups_x, ea_speedups_y = [], []
        gen = 0
        t_base = None
        while True:
            gen_dir = os.path.join(ea_results_dir, f"gen_{gen}")
            all_csv = os.path.join(gen_dir, "all.csv")
            if not os.path.exists(all_csv):
                break
            dfe = pd.read_csv(all_csv)
            if "runtime_seconds" in dfe.columns:
                t = dfe["runtime_seconds"].max()
                if t_base is None:
                    t_base = t
                if t_base and t_base > 0:
                    ea_speedups_x.append(gen + 1)
                    ea_speedups_y.append(t_base / t)
            gen += 1
        if ea_speedups_x:
            ax.plot(ea_speedups_x, ea_speedups_y, "s-", label="EA (generacje)")

    ax.set_xlabel("Liczba workerów / iteracji")
    ax.set_ylabel("Speedup")
    ax.set_title("Speedup: MC vs EA")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = os.path.join(output_dir, "mc_convergence.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot_mc_convergence] saved {out}")


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/mc", help="Dir with MC result CSVs.")
    p.add_argument("--ea-dir", default=None, help="Dir with gen_0/, gen_1/,... for EA comparison.")
    p.add_argument("--output-dir", default="results/plots")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    plot_mc_convergence(args.results_dir, args.output_dir, args.ea_dir)


if __name__ == "__main__":
    main()
