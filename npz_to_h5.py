import h5py
import numpy as np
import argparse
import os
import glob
import natsort

def concat_npz_events_to_h5(input_dir, output_file, normalize_time=False):
    npz_files = natsort.natsorted(glob.glob(os.path.join(input_dir, "*.npz")))
    if not npz_files:
        print("No NPZ files found in input directory.")
        return

    print(f"Found {len(npz_files)} NPZ files. Converting...")

    with h5py.File(output_file, "w") as h5f:
        dsets = {}
        time_offset = 0  # ensures continuous timestamps if enabled

        for idx, npz_file in enumerate(npz_files):
            print(f"[{idx+1}/{len(npz_files)}] Loading {npz_file}")

            with np.load(npz_file) as data:
                for key, arr in data.items():

                    # Normalize timestamps if requested
                    if normalize_time and key.lower().startswith("t"):
                        arr = arr - arr[0] + time_offset
                        time_offset = arr[-1] + 1

                    # First file creates datasets
                    if key not in dsets:
                        dsets[key] = h5f.create_dataset(
                            key,
                            shape=(arr.shape[0],),
                            maxshape=(None,),
                            dtype=arr.dtype,
                            compression="gzip",
                            compression_opts=4,
                            chunks=True
                        )
                        dsets[key][:] = arr

                    else:
                        # Extend and append
                        old_size = dsets[key].shape[0]
                        new_size = old_size + arr.shape[0]
                        dsets[key].resize((new_size,))
                        dsets[key][old_size:new_size] = arr

    print("Finished Conversion")
    print(f"Output HDF5 file: {output_file}")
    print(f"Stored keys: {list(dsets.keys())}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Concatenate NPZ event files into a single HDF5 file.")
    parser.add_argument("--input_dir",type=str,required=True,help="Directory containing NPZ files.")
    parser.add_argument("--output_file",type=str,required=True,help="Output HDF5 file path.")
    parser.add_argument("--normalize_time",action="store_true",help="Normalize and concatenate timestamps continuously.")

    args = parser.parse_args()

    # Safety warning if overwriting
    if os.path.exists(args.output_file):
        print(f"Warning: {args.output_file} already exists and will be overwritten.")

    concat_npz_events_to_h5(args.input_dir, args.output_file, args.normalize_time)
