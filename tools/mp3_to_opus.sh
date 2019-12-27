# This script converts a folder with .mp3s into a folder of 96k .opus

#! /usr/bin/env bash

if [ "$#" -ne 2 ]; then
    echo "Usage: ./mp3_to_opus.sh SRC_DIR TGT_DIR"
	exit 1
fi

SRC_DIR=$1
TGT_DIR=$2

for file in "$SRC_DIR"/*.mp3;
do
	TGT_FILE="$TGT_DIR/$(basename "$file" .mp3).opus"
	ffmpeg -i "$file" -c:a libopus -b:a 96k "$TGT_FILE"
done
