import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def _load(path):
    if path and os.path.exists(path):
        return pd.read_csv(path)
    return None


def plot_comparison(random_csv, grid_csv, ea_csv_last, ea_all_gens_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    dfs = {}
    labels = ["Random Search", "Grid Search", "EA"]
    paths = [random_csv, grid_csv, ea_csv_last]
    for label, path in zip(labels, paths):
        df = _load(path)
        if df is not None and "avg_waiting_time" in df.columns:
            dfs[label] = df["avg_waiting_time"].dropna()

    if not dfs:
        print("[plot_comparison] Brak danych do wykresu.")
        return

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("EA vs Random Search vs Grid Search (budżet 300 symulacji)", fontsize=13)

    ax = axes[0]
    names = list(dfs.keys())
    bests = [dfs[n].min() for n in names]
    means = [dfs[n].mean() for n in names]
    worsts = [dfs[n].max() for n in names]
    x = np.arange(len(names))
    w = 0.25
    ax.bar(x - w, bests, w, label="Najlepszy", color="tab:green")
    ax.bar(x, means, w, label="Średni", color="tab:blue")
    ax.bar(x + w, worsts, w, label="Najgorszy", color="tab:red")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.set_ylabel("avg_waiting_time [s]")
    ax.set_title("Porównanie wyników")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    ax = axes[1]
    for name, series in dfs.items():
        sorted_vals = np.sort(series)
        cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
        ax.plot(sorted_vals, cdf, label=name)
    ax.set_xlabel("avg_waiting_time [s]")
    ax.set_ylabel("CDF")
    ax.set_title("Rozkład jakości (CDF)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[2]
    if ea_all_gens_dir and os.path.isdir(ea_all_gens_dir):
        cumulative = 0
        xs, ys = [], []
        gen = 0
        while True:
            gen_dir = os.path.join(ea_all_gens_dir, f"gen_{gen}")
            all_csv = os.path.join(gen_dir, "all.csv")
            if not os.path.exists(all_csv):
                break
            df = pd.read_csv(all_csv)
            if "avg_waiting_time" in df.columns:
                cumulative += len(df)
                xs.append(cumulative)
                ys.append(df["avg_waiting_time"].min())
            gen += 1
        if xs:
            ax.plot(xs, ys, "o-", label="EA best")

    if "Random Search" in dfs:
        n = len(dfs["Random Search"])
        running_min = [dfs["Random Search"].iloc[:i + 1].min() for i in range(n)]
        ax.plot(range(1, n + 1), running_min, "--", alpha=0.7, label="Random best-so-far")
    if "Grid Search" in dfs:
        n = len(dfs["Grid Search"])
        running_min = [dfs["Grid Search"].iloc[:i + 1].min() for i in range(n)]
        ax.plot(range(1, n + 1), running_min, "-.", alpha=0.7, label="Grid best-so-far")

    ax.set_xlabel("Liczba symulacji")
    ax.set_ylabel("Najlepszy avg_waiting_time [s]")
    ax.set_title("Krzywa uczenia")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = os.path.join(output_dir, "search_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot_comparison] saved {out}")


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--random", default=None, help="CSV z wynikami random search.")
    p.add_argument("--grid", default=None, help="CSV z wynikami grid search.")
    p.add_argument("--ea", default=None, help="CSV z wynikami ostatniej generacji EA.")
    p.add_argument("--ea-dir", default=None, help="Katalog z gen_0/, gen_1/, ... dla EA.")
    p.add_argument("--output-dir", default="results/plots")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    plot_comparison(args.random, args.grid, args.ea, args.ea_dir, args.output_dir)


if __name__ == "__main__":
    main()
