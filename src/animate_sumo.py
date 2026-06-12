import argparse
import os
import sys
import xml.etree.ElementTree as ET

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.animation as animation
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.io import ensure_dir, load_json
from utils.network import parse_junction_positions, parse_tl_junction_ids

FPS = 8
MAX_FRAMES = 180


def _load_fcd(fcd_path):
    frames = []
    current_time = None
    current_vehicles = []
    for event, elem in ET.iterparse(fcd_path, events=("start", "end")):
        if event == "start" and elem.tag == "timestep":
            current_time = float(elem.get("time", 0))
            current_vehicles = []
        elif event == "start" and elem.tag == "vehicle":
            try:
                current_vehicles.append((
                    elem.get("id", ""),
                    float(elem.get("x", 0)),
                    float(elem.get("y", 0)),
                    float(elem.get("speed", 0)),
                ))
            except (TypeError, ValueError):
                pass
        elif event == "end" and elem.tag == "timestep":
            frames.append((current_time, current_vehicles))
            elem.clear()
        if len(frames) >= MAX_FRAMES:
            break
    return frames


def _tl_color(t, config, junction_index):
    offsets = config.get("offsets")
    if offsets and junction_index < len(offsets):
        offset = int(offsets[junction_index])
    else:
        offset = int(config.get("offset", 0))

    cycle = int(config.get("cycle_length", 60))
    green_ns = int(config.get("green_ns", 30))
    green_ew = int(config.get("green_ew", 25))
    yellow = int(config.get("yellow_time", 3))
    all_red = int(config.get("all_red_time", 2))

    t_in_cycle = (int(t) - offset) % cycle

    if t_in_cycle < green_ns:
        return "lime"
    elif t_in_cycle < green_ns + yellow:
        return "yellow"
    elif t_in_cycle < green_ns + yellow + all_red:
        return "red"
    elif t_in_cycle < green_ns + yellow + all_red + green_ew:
        return "deepskyblue"
    else:
        return "red"


def _make_axes(fig, rect, title, junction_pos, tl_ids, config, frames, speed_max):
    ax = fig.add_axes(rect)
    ax.set_facecolor("#1a1a2e")
    ax.set_title(title, color="white", fontsize=11, pad=4)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

    if not junction_pos:
        return ax, None, []

    xs = [p[0] for p in junction_pos.values()]
    ys = [p[1] for p in junction_pos.values()]
    margin = max((max(xs) - min(xs)), (max(ys) - min(ys))) * 0.15 + 50
    ax.set_xlim(min(xs) - margin, max(xs) + margin)
    ax.set_ylim(min(ys) - margin, max(ys) + margin)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]", color="#aaa", fontsize=8)
    ax.set_ylabel("y [m]", color="#aaa", fontsize=8)

    tl_circles = []
    for i, jid in enumerate(tl_ids):
        if jid not in junction_pos:
            continue
        x, y = junction_pos[jid]
        circle = plt.Circle((x, y), radius=18, color="lime", zorder=3)
        ax.add_patch(circle)
        ax.text(x, y, jid, color="black", fontsize=5, ha="center", va="center", zorder=4)
        tl_circles.append((i, circle))

    scatter = ax.scatter([], [], c=[], cmap="RdYlGn", vmin=0, vmax=speed_max,
                         s=8, zorder=5, alpha=0.85)

    ns_patch = mpatches.Patch(color="lime", label="NS green")
    ew_patch = mpatches.Patch(color="deepskyblue", label="EW green")
    y_patch = mpatches.Patch(color="yellow", label="Yellow")
    r_patch = mpatches.Patch(color="red", label="Red")
    ax.legend(handles=[ns_patch, ew_patch, y_patch, r_patch],
              loc="upper right", fontsize=6, framealpha=0.3,
              labelcolor="white", facecolor="#333")

    return ax, scatter, tl_circles


def _animate(fcd_path, net_path, config, title="Traffic Simulation"):
    frames = _load_fcd(fcd_path)
    junction_pos = parse_junction_positions(net_path) if net_path else {}
    tl_ids = parse_tl_junction_ids(net_path) if net_path else []

    all_speeds = [spd for _, vehicles in frames for _, _, _, spd in vehicles]
    speed_max = max(all_speeds) if all_speeds else 14.0

    return frames, junction_pos, tl_ids, speed_max


def render_single(fcd_path, net_path, config, output_path, title="Traffic Simulation"):
    frames, junction_pos, tl_ids, speed_max = _animate(fcd_path, net_path, config, title)

    fig = plt.figure(figsize=(7, 6), facecolor="#0d0d1a")
    ax, scatter, tl_circles = _make_axes(
        fig, [0.08, 0.08, 0.88, 0.82], title,
        junction_pos, tl_ids, config, frames, speed_max,
    )
    time_text = ax.text(0.02, 0.97, "", transform=ax.transAxes,
                        color="white", fontsize=9, va="top")

    def update(frame_idx):
        t, vehicles = frames[frame_idx]
        if vehicles:
            xs = np.array([v[1] for v in vehicles])
            ys = np.array([v[2] for v in vehicles])
            spds = np.array([v[3] for v in vehicles])
            scatter.set_offsets(np.column_stack([xs, ys]))
            scatter.set_array(spds)
        else:
            scatter.set_offsets(np.empty((0, 2)))
        for i, circle in tl_circles:
            circle.set_color(_tl_color(t, config, i))
        time_text.set_text(f"t = {int(t)} s   vehicles = {len(vehicles)}")
        return [scatter, time_text] + [c for _, c in tl_circles]

    ani = animation.FuncAnimation(fig, update, frames=len(frames), interval=1000 // FPS, blit=True)
    ensure_dir(output_path)
    ani.save(output_path, writer=animation.PillowWriter(fps=FPS))
    plt.close()
    print(f"[animate_sumo] wrote {output_path} ({len(frames)} frames)")


def render_comparison(
    fcd_a, net_path, config_a, title_a,
    fcd_b, config_b, title_b,
    output_path,
):
    frames_a, junction_pos, tl_ids, speed_max_a = _animate(fcd_a, net_path, config_a)
    frames_b, _, _, speed_max_b = _animate(fcd_b, net_path, config_b)
    speed_max = max(speed_max_a, speed_max_b)

    n_frames = min(len(frames_a), len(frames_b))

    fig = plt.figure(figsize=(14, 6), facecolor="#0d0d1a")
    ax_a, sc_a, circles_a = _make_axes(
        fig, [0.03, 0.08, 0.44, 0.82], title_a,
        junction_pos, tl_ids, config_a, frames_a, speed_max,
    )
    ax_b, sc_b, circles_b = _make_axes(
        fig, [0.53, 0.08, 0.44, 0.82], title_b,
        junction_pos, tl_ids, config_b, frames_b, speed_max,
    )
    time_text = fig.text(0.5, 0.02, "", ha="center", color="white", fontsize=10)

    def update(fi):
        for sc, circles, frames, config in [
            (sc_a, circles_a, frames_a, config_a),
            (sc_b, circles_b, frames_b, config_b),
        ]:
            t, vehicles = frames[fi]
            if vehicles:
                xs = np.array([v[1] for v in vehicles])
                ys = np.array([v[2] for v in vehicles])
                spds = np.array([v[3] for v in vehicles])
                sc.set_offsets(np.column_stack([xs, ys]))
                sc.set_array(spds)
            else:
                sc.set_offsets(np.empty((0, 2)))
            for i, circle in circles:
                circle.set_color(_tl_color(t, config, i))
        t_a = frames_a[fi][0]
        time_text.set_text(f"t = {int(t_a)} s")
        return [sc_a, sc_b, time_text] + [c for _, c in circles_a] + [c for _, c in circles_b]

    ani = animation.FuncAnimation(fig, update, frames=n_frames, interval=1000 // FPS, blit=True)
    ensure_dir(output_path)
    ani.save(output_path, writer=animation.PillowWriter(fps=FPS))
    plt.close()
    print(f"[animate_sumo] wrote comparison {output_path} ({n_frames} frames)")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Animate SUMO FCD output as traffic GIF.")
    parser.add_argument("--fcd", required=True, help="Path to SUMO FCD XML file.")
    parser.add_argument("--network", default=None, help="Path to SUMO net.xml for layout.")
    parser.add_argument("--config", required=True, help="Path to config JSON (for TL phases).")
    parser.add_argument("--output", required=True, help="Output GIF path.")
    parser.add_argument("--title", default="Traffic Simulation", help="Plot title.")
    parser.add_argument("--compare-fcd", default=None, help="Second FCD for side-by-side mode.")
    parser.add_argument("--compare-config", default=None, help="Config for second FCD.")
    parser.add_argument("--compare-title", default="EA Best", help="Title for second panel.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    config = load_json(args.config)

    if args.compare_fcd:
        config_b = load_json(args.compare_config) if args.compare_config else config
        render_comparison(
            fcd_a=args.fcd,
            net_path=args.network,
            config_a=config,
            title_a=args.title,
            fcd_b=args.compare_fcd,
            config_b=config_b,
            title_b=args.compare_title,
            output_path=args.output,
        )
    else:
        render_single(
            fcd_path=args.fcd,
            net_path=args.network,
            config=config,
            output_path=args.output,
            title=args.title,
        )


if __name__ == "__main__":
    main()
