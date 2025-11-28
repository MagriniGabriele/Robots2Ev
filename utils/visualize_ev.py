#!/usr/bin/env python3
import argparse
import glob
import numpy as np
import os
import matplotlib.pyplot as plt
import natsort
import time

def add_events_to_image(shape, events):
    """
    Creates an image from events for the current frame only.
    shape: [H, W]
    events: dict with x, y, p arrays
    """
    H, W = shape
    img = np.zeros((H, W, 3), dtype=np.uint8)
    xs = events["x"]
    ys = events["y"]
    ps = events["p"]
    img[ys, xs, :] = 128
    img[ys, xs, ps] = 255
    return img

def decay_image(img, decay_value=5):
    """Optional: fade the image (applied per frame)"""
    img[:] = np.clip(img - decay_value, 0, 255)
    return img

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Frame-wise accumulated DVS event viewer")
    parser.add_argument("--input_dir", required=True, help="Folder containing .npz event files")
    parser.add_argument("--shape", nargs=2, type=int, default=[720, 1280], help="H W")
    parser.add_argument("--fps", type=int, default=30, help="Display FPS")
    parser.add_argument("--decay", type=int, default=0, help="Optional decay per frame")
    args = parser.parse_args()

    H, W = args.shape
    frame_interval = 1.0 / args.fps
    last_update = time.time()

    # Collect folders (pick one randomly if multiple)
    folders = [f for f in sorted(glob.glob(os.path.join(args.input_dir, "*"))) if os.path.isdir(f)]
    if len(folders) == 0:
        raise ValueError("No folders found in input_dir")

    chosen_folder = folders[np.random.randint(len(folders))]
    print("Using folder:", chosen_folder)

    event_files = natsort.natsorted(glob.glob(os.path.join(chosen_folder, "*.npz")))
    if len(event_files) == 0:
        raise ValueError("No .npz files found in the folder")

    # Initialize display
    plt.ion()
    fig, ax = plt.subplots()
    img_buffer = np.zeros((H, W, 3), dtype=np.uint8)
    handle = ax.imshow(img_buffer)
    ax.axis('off')
    plt.show(block=False)

    # Frame-wise accumulation
    for f in event_files:
        events = np.load(f)

        # Add events to temporary frame buffer
        frame_img = add_events_to_image([H, W], events)

        # Optional decay applied per frame
        if args.decay > 0:
            frame_img = decay_image(frame_img, decay_value=args.decay)

        # Merge frame buffer with display buffer
        img_buffer = frame_img

        now = time.time()
        if now - last_update >= frame_interval:
            handle.set_data(img_buffer)
            plt.pause(0.001)  # refresh GUI
            last_update = now
