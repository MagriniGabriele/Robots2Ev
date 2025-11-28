import argparse
import glob
import numpy as np
import os
import matplotlib.pyplot as plt
import cv2
import natsort

def render(x, y, t, p, shape):
    # create black image
    img = np.zeros(shape + [3], dtype="uint8")
    # if polarity is 1, set pixel to blue, else red
    for xi, yi, ti, pi in zip(x, y, t, p):
        if pi == 1:
            img[yi, xi] = [0, 0, 255]
        else:
            img[yi, xi] = [255, 0, 0]
    return img

if __name__ == "__main__":
    parser = argparse.ArgumentParser("""Generate events from a high frequency video stream""")
    parser.add_argument("--input_dir", default="")
    parser.add_argument("--output_dir", default="")
    parser.add_argument("--shape", nargs=2, default=[180, 320])
    args = parser.parse_args()

    event_files = natsort.natsorted(glob.glob(os.path.join(args.input_dir, "*.npz")))

    # first image is blank
    fig, ax = plt.subplots()
    img = np.full(shape=args.shape + [3], fill_value=0, dtype="uint8")
    
    # save img to output dir (same shape as og frames)
    cv2.imwrite(os.path.join(args.output_dir, "frame_00000.png"), img)    
    
    # then go through events
    for index,f in enumerate(event_files):
        events = np.load(f)
        img = render(shape=args.shape, **events)
        cv2.imwrite(os.path.join(args.output_dir, f"frame_{(index+1):05d}.png"), img)


        