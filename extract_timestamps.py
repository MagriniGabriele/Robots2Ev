import os
import argparse

def generate_timestamps(folder, fps, output_file="timestamps.txt"):
    # Count number of .png files
    png_files = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
    png_files.sort()  # Ensure correct order if filenames are ordered numerically
    num_frames = len(png_files)

    if num_frames == 0:
        print("No PNG images found in the folder.")
        return

    # Compute timestamps
    timestamps = [(i / fps) for i in range(num_frames)]

    # Save to txt file
    output_path = os.path.join(folder, output_file)
    with open(output_path, "w") as f:
        for t in timestamps:
            f.write(f"{t}\n")

    # Display video length
    video_length = num_frames / fps
    print(f"Found {num_frames} frames at {fps} FPS.")
    print(f"Total video length: {video_length:.3f} seconds.")
    print(f"Timestamps saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate timestamps for PNG sequence based on FPS.")
    parser.add_argument("--folder", type=str, help="Path to folder containing PNG images.")
    parser.add_argument("--fps", type=float, required=True, help="Frames per second of the video.")
    parser.add_argument("--output", type=str, default="timestamps.txt", help="Output text file name.")
    args = parser.parse_args()

    generate_timestamps(args.folder, args.fps, args.output)
