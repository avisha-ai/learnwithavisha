#!/bin/bash
# ep001_the_drift — grade, pad to the recipe's runtime, lay back the mix.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ENG="$(cd "$HERE/../.." && pwd)"
BIN=/Users/mrinalgala/Documents/Avisha/learnwithavisha/.micromamba/root/envs/manim/bin
OUT="$ENG/_render"
SRC="$OUT/videos/render/1080p60/Ep001.mp4"
FRAMES=$("$BIN/python" -c "import json;print(int(json.load(open('$HERE/episode.json'))['runtime']*60))")

"$ENG/engine/grade.sh" "$SRC" "$OUT/_graded.mp4"
"$BIN/python" -c "
import sys, json; sys.path.insert(0, '$ENG')
from engine.scene import Stage
from engine.sound import mix_episode
ep = json.load(open('$HERE/episode.json'))
mix_episode(Stage(ep), '$OUT/ep001_bed.wav')
print('mix written')"

"$BIN/ffmpeg" -v error -i "$OUT/_graded.mp4" -i "$OUT/ep001_bed.wav" \
  -filter_complex "[0:v]tpad=stop_mode=clone:stop_duration=1[v]" \
  -map "[v]" -map 1:a -frames:v "$FRAMES" -r 60 \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -y "$OUT/ep001_the_drift.mp4"
"$BIN/ffprobe" -v error -show_entries format=duration \
  -show_entries stream=codec_type,width,height,nb_frames -of default=nw=1 \
  "$OUT/ep001_the_drift.mp4"
