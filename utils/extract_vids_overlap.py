#!/usr/bin/env python3
import argparse
import os
import glob
import numpy as np
import natsort
import imageio
from pathlib import Path
import cv2


def render_events(shape, events):
    """Render a single event frame."""
    H, W = shape
    img = np.zeros((H, W, 3), dtype=np.uint8)

    xs, ys, ps = events["x"], events["y"], events["p"]

    img[ys, xs, :] = 128
    img[ys, xs, ps] = 255
    return img


def find_event_folders(root):
    """Return list of all subfolders that contain .npz files."""
    event_dirs = []
    for dirpath, _, files in os.walk(root):
        if any(f.endswith(".npz") for f in files):
            event_dirs.append(dirpath)
    return event_dirs


def make_output_path(input_root, output_root, folder):
    """
    Build mirrored folder structure:
      input_root/f1/f2/...  →  output_root/f1/f2/...
    """
    rel = os.path.relpath(folder, input_root)
    out_dir = os.path.join(output_root, rel)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def render_folder_to_video(folder, out_dir, shape, fps, ext):
    """Render all npz in a folder to gif or mp4."""
     # first get ev frames
    npz_files = natsort.natsorted(glob.glob(os.path.join(folder, "*.npz")))
    # now get rgb frames
    rgb_files = natsort.natsorted(glob.glob(os.path.join(folder.replace("/EV", ""), "*.png")))

    if not npz_files:
        print(f"[SKIP] No npz in {folder}")
        return

    print(f"[INFO] Rendering {folder} → {out_dir}")

    frames_ev = []
    for f in npz_files:
        events = np.load(f)
        img = render_events(shape, events)
        frames_ev.append(img)

    frames_rgb = [imageio.imread(f) for f in rgb_files]

    # create overlap frames
    frames = []
    for ev_frame, rgb_frame in zip(frames_ev, frames_rgb):
        overlap_frame = cv2.addWeighted(ev_frame, 0.7, rgb_frame, 0.3, 0)
        frames.append(overlap_frame)

    output_path = os.path.join(out_dir, f"events.{ext}")

    if ext == "gif":
        imageio.mimsave(output_path, frames, fps=fps)
    else:
        imageio.mimsave(output_path, frames, fps=fps, codec='libx264')

    print(f"[DONE] Saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Batch render event folders to GIF/MP4")
    parser.add_argument("--input_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--shape", nargs=2, type=int, default=[720, 1280])
    parser.add_argument("--fps", type=int, default=120)
    parser.add_argument("--ext", choices=["gif", "mp4"], default="mp4")
    args = parser.parse_args()

    H, W = args.shape

    # 1. Find all folders containing npz files
    event_folders = find_event_folders(args.input_dir)
    print(f"Found {len(event_folders)} folders with NPZ files.")

    # 2. Process each folder
    for folder in event_folders:
        out_dir = make_output_path(args.input_dir, args.output_dir, folder)
        render_folder_to_video(folder, out_dir, [H, W], args.fps, args.ext)
