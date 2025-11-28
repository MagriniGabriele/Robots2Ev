#!/usr/bin/env python3
import os
import glob
import numpy as np
import argparse 


parser = argparse.ArgumentParser(description="Generate mirrored directory structure with symlinks and timestamps.")
parser.add_argument("--input_root", type=str, required=True, help="Root directory containing source image folders.")
parser.add_argument("--output_root", type=str, default="tmp_upsampled_rgb", help="Output root directory for mirrored structure.")
parser.add_argument("--dt", type=float, default=1/120, help="Time difference between frames in seconds.")
args = parser.parse_args()
# === USER CONFIG ===
INPUT_ROOT = args.input_root          # root containing symlinked folders
OUTPUT_ROOT = args.output_root        # where to create mirrored tree with imgs/ symlinks
DT = args.dt                # timestamp spacing in seconds (set to your dt)
# ===================

def find_pngs(dir_path):
    return sorted(glob.glob(os.path.join(dir_path, "*.png")))

os.makedirs(OUTPUT_ROOT, exist_ok=True)

visited_realpaths = set()

# Use followlinks so python enters symlinked directories, but avoid reprocessing real dirs.
for path, subdirs, files in os.walk(INPUT_ROOT, followlinks=True):
    try:
        real = os.path.realpath(path)
    except Exception:
        real = path

    # Skip if we've already processed this real directory (prevents loops & duplicates)
    if real in visited_realpaths:
        continue
    visited_realpaths.add(real)

    # If this directory name is "imgs", then the actual sequence parent is the parent dir.
    # We want to mirror the parent into OUTPUT_ROOT/<rel_to_INPUT_ROOT>/timestamps.txt and imgs/
    if os.path.basename(path) == "imgs":
        seq_dir = os.path.dirname(path)
        png_dir = path                       # pngs are inside this 'imgs' folder
        rel = os.path.relpath(seq_dir, INPUT_ROOT)
    else:
        # Normal case: frames might be directly in 'path'
        pngs_here = find_pngs(path)
        if len(pngs_here) == 0:
            # no pngs directly here -> continue
            continue
        seq_dir = path
        png_dir = path
        rel = os.path.relpath(seq_dir, INPUT_ROOT)

    # Compose output paths that mirror input structure
    out_seq_dir = os.path.join(OUTPUT_ROOT, rel)
    out_imgs_dir = os.path.join(out_seq_dir, "imgs")
    os.makedirs(out_imgs_dir, exist_ok=True)

    # Collect frames from source png_dir (which may be an 'imgs' folder or the folder itself)
    frames = find_pngs(png_dir)
    if len(frames) == 0:
        # nothing to do
        continue

    print(f"\nProcessing source: {path}")
    print(f"  real: {real}")
    print(f"  sequence dir mirrored to: {out_seq_dir}")
    print(f"  found {len(frames)} frames in: {png_dir}")

    # Create symlinks in output imgs/ pointing to the absolute path of the originals
    for src in frames:
        link_name = os.path.join(out_imgs_dir, os.path.basename(src))
        if os.path.exists(link_name):
            # if exists and is a symlink pointing to same target, skip; otherwise warn and skip
            if os.path.islink(link_name):
                # optional: verify same target
                existing_target = os.path.realpath(link_name)
                if existing_target == os.path.realpath(src):
                    continue
                else:
                    print(f"  WARNING: link {link_name} exists and points to different target; skipping.")
                    continue
            else:
                print(f"  WARNING: path {link_name} exists and is not a symlink; skipping.")
                continue

        # Create symlink (absolute target avoids relative path weirdness)
        try:
            os.symlink(os.path.abspath(src), link_name)
        except FileExistsError:
            pass
        except OSError as e:
            print(f"  ERROR creating symlink {link_name} -> {src}: {e}")
            continue

    # Generate timestamps file at out_seq_dir/timestamps.txt
    timestamps = np.arange(len(frames)) * DT
    ts_path = os.path.join(out_seq_dir, "timestamps.txt")
    np.savetxt(ts_path, timestamps, fmt="%.9f")
    print(f"  -> created imgs symlinks at {out_imgs_dir}")
    print(f"  -> wrote timestamps: {ts_path}")
