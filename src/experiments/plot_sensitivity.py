import argparse
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

COMBOS = [
    (300, 1), (150, 2), (100, 3), (60, 5), (50, 6), (30, 10), (15, 20),
]


def _load_best_per_gen(base_dir, pop, gen_total):
    label = f"pop{pop}_gen{gen_total}"
    d = os.path.join(base_dir, label)
    if not os.path.isdir(d):
        return None, label
    bests = []
    for g in range(gen_total):
        csv = os.path.join(d, f"gen_{g}", "all.csv")
        if not os.path.exists(csv):
            break
        df = pd.read_csv(csv)
        if "avg_waiting_time" in df.columns:
            bests.append(df["avg_waiting_time"].min())
    return bests, label


def plot_sensitivity(results_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Analiza wrażliwości parametrów EA (budżet 300 symulacji)", fontsize=13)

    ax_lines = axes[0]
    ax_pop = axes[1]
    ax_gen = axes[2]

    pop_best = []
    gen_best = []

    for pop, n_gen in COMBOS:
        bests, label = _load_best_per_gen(results_dir, pop, n_gen)
        if not bests:
            pop_best.append((pop, n_gen, None))
            gen_best.append((pop, n_gen, None))
            continue
        ax_lines.plot(range(1, len(bests) + 1), bests, "o-", label=label)
        pop_best.append((pop, n_gen, bests[-1]))
        gen_best.append((pop, n_gen, bests[-1]))

    ax_lines.set_xlabel("Generacja")
    ax_lines.set_ylabel("Najlepszy avg_waiting_time [s]")
    ax_lines.set_title("Konwergencja EA dla różnych parametrów")
    ax_lines.legend(fontsize=7, ncol=2)
    ax_lines.grid(True, alpha=0.3)

    pops_ok = [(p, v) for p, g, v in pop_best if v is not None]
    if pops_ok:
        pops, vals = zip(*pops_ok)
        ax_pop.scatter(pops, vals, c=vals, cmap="RdYlGn_r", s=80, zorder=3)
        ax_pop.plot(pops, vals, "k--", alpha=0.4)
        ax_pop.set_xlabel("Rozmiar populacji (pop_size)")
        ax_pop.set_ylabel("Najlepszy wynik (ostatnia gen)")
        ax_pop.set_title("pop_size vs jakość")
        ax_pop.grid(True, alpha=0.3)
    else:
        ax_pop.text(0.5, 0.5, "Brak danych", ha="center", va="center", transform=ax_pop.transAxes)

    gens_ok = [(g, v) for p, g, v in gen_best if v is not None]
    if gens_ok:
        gs, vals = zip(*gens_ok)
        ax_gen.scatter(gs, vals, c=vals, cmap="RdYlGn_r", s=80, zorder=3)
        ax_gen.plot(gs, vals, "k--", alpha=0.4)
        ax_gen.set_xlabel("Liczba generacji (n_gen)")
        ax_gen.set_ylabel("Najlepszy wynik (ostatnia gen)")
        ax_gen.set_title("n_gen vs jakość")
        ax_gen.grid(True, alpha=0.3)
    else:
        ax_gen.text(0.5, 0.5, "Brak danych", ha="center", va="center", transform=ax_gen.transAxes)

    plt.tight_layout()
    out = os.path.join(output_dir, "sensitivity.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[plot_sensitivity] saved {out}")


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", default="results/sensitivity",
                   help="Dir with pop{P}_gen{G}/ subdirs.")
    p.add_argument("--output-dir", default="results/plots")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    plot_sensitivity(args.results_dir, args.output_dir)


if __name__ == "__main__":
    main()
