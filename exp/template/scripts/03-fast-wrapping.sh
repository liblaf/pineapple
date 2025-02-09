#!/bin/bash
set -o errexit
set -o nounset
set -o pipefail

GIT_ROOT=$(git rev-parse --show-toplevel)
SOURCE_DIR="$GIT_ROOT/data/template/02-rigid/wrap"
TARGET_DIR="$GIT_ROOT/data/template/01-upright/sculptor"
OUTPUT_DIR="$GIT_ROOT/data/template/03-wrapped/wrap"

for source_file in "$SOURCE_DIR"/*.ply; do
  name="$(basename --suffix=".ply" -- "$source_file")"
  echo "Fast Wrapping \"$name\" ..."
  python src/03-fast-wrapping.py --output "$OUTPUT_DIR/$name.ply" "$source_file" "$TARGET_DIR/$name.ply"
done
