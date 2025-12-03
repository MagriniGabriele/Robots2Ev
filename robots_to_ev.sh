#!/bin/bash

source /home/gmagrini/miniconda3/etc/profile.d/conda.sh 
conda activate vid2e

export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0

HOME_DIR="$1"
GENERATE_FRAMES="false"  # set to "true" to enable frame extraction after EV generation

# views to simulate in events
TARGETS=("ego1L" "ego2L" "exoL")

# per-target img_size: height width. Only exo by default is full original scale
declare -A IMG_SIZES
IMG_SIZES=(
    ["ego1L"]="360 640"
    ["ego2L"]="360 640"
    ["exoL"]="720 1280"
)

if [[ -z "$HOME_DIR" ]]; then
    echo "Usage: $0 <home_dir>"
    exit 1
fi

# get the unique set of directories that contain .png files
mapfile -t dirs < <(find "$HOME_DIR" -type f -name '*.png' -printf '%h\n' | sort -u)

for dir in "${dirs[@]}"; do
    target_name=$(basename "$dir")

    # skip if target not in TARGETS
    if [[ ! " ${TARGETS[*]} " =~ " ${target_name} " ]]; then
        echo "Skipping directory: $dir"
        continue
    fi

    # select image size
    IMG_SIZE="${IMG_SIZES[$target_name]}"
    if [[ -z "$IMG_SIZE" ]]; then
        echo "ERROR: No img_size defined for target '$target_name'"
        exit 1
    fi

    # EV directory is at the same level of view folders (for the moment)
    EV_DIR="$dir/../EV"
    echo "Processing: $dir"
    echo "Creating directory: $EV_DIR"

    # create output directories and temporal directory for intermediate files
    mkdir -p "$EV_DIR/"
    mkdir -p "$EV_DIR/tmp"
    mkdir -p "$EV_DIR/$target_name"

    # check if target EV folder already exists, skip if it does
    if [ -d "$EV_DIR/$target_name" ] && [ "$(ls -A $EV_DIR/$target_name)" ]; then
        echo "EV folder already exists and is not empty. Skipping: $EV_DIR/$target_name"
        continue
    fi

    # generate temporary ordered frames & timestamps (symlinking them to tmp folder)
    python generate_format.py --input_root "$dir" --output_root "$EV_DIR/tmp"

    # run event simulation
    python rpg_vid2e/esim_torch/scripts/generate_events_general.py \
        --input_dir="$EV_DIR/tmp" \
        --output_dir="$EV_DIR/$target_name" \
        --contrast_threshold_negative=0.2 \
        --contrast_threshold_positive=0.2 \
        --refractory_period_ns=0 \
        --img_size $IMG_SIZE

    echo "Finished processing: $dir"
done


# OPTIONAL: extract frames from the generated EV folders to verify correctness
if [[ "$GENERATE_FRAMES" == "true" ]]; then    
    for dir in "${dirs[@]}"; do

        # skip if target not in TARGETS
        if [[ ! " ${TARGETS[*]} " =~ " ${target_name} " ]]; then
            echo "Skipping directory: $dir"
            continue
        fi  

        echo "Extracting frames from: $EV_DIR"
        
        # frames are at the same level of EV folders
        EV_DIR="$dir/../EV/$(basename "$dir")"
        FRAMES_DIR="$dir/../EV_frames/$(basename "$dir")"
        mkdir -p "$FRAMES_DIR"

        # create frames based on single npz files (one for each corresponding rgb frame)
        python npz_to_frames.py --input_dir "$EV_DIR" --output_dir "$FRAMES_DIR"
        
        echo "Finished extracting frames to: $FRAMES_DIR"
    done
fi