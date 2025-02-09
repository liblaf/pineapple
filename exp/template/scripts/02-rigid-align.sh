#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

GIT_ROOT=$(git rev-parse --show-toplevel)
SOURCE_DIR="$GIT_ROOT/data/template/00-raw/wrap"
TARGET_DIR="$GIT_ROOT/data/template/01-upright/sculptor"
OUTPUT_DIR="$GIT_ROOT/data/template/02-rigid/wrap"

for source_file in "$SOURCE_DIR"/*.obj; do
  name="$(basename --suffix=".obj" -- "$source_file")"
  echo "Rigid aligning $name ..."
  python src/02-rigid-align.py --output "$OUTPUT_DIR/$name.ply" "$source_file" "$TARGET_DIR/$name.ply"
done
