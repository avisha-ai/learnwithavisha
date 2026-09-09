#!/bin/bash
# Visual Pilot 001 — finish and lay back sound.
#   1. grade the Manim render (bloom / vignette / grain)
#   2. pad to exactly 27.000 s (Manim lands a few frames short)
#   3. mux the procedural plant bed
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="$HERE/../output/visual_pilot_001"
BIN=/Users/mrinalgala/Documents/Avisha/learnwithavisha/.micromamba/root/envs/manim/bin
SRC="$OUT/media/videos/pilot001/1080p60/Pilot001.mp4"
GRADED="$OUT/_graded.mp4"
FINAL="$OUT/pilot001_v1.mp4"

"$HERE/grade.sh" "$SRC" "$GRADED"

"$BIN/ffmpeg" -v error \
  -i "$GRADED" -i "$OUT/plant_bed.wav" \
  -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=1[v]" \
  -map "[v]" -map 1:a -frames:v 1620 -r 60 \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart -y "$FINAL"

"$BIN/ffprobe" -v error -show_entries format=duration \
  -show_entries stream=codec_type,width,height,nb_frames,channels \
  -of default=nw=1 "$FINAL"
