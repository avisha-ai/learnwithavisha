#!/bin/bash
# Render every style frame for this episode, grade it, and put it somewhere
# a human can actually find it. Manim writes into _render/, which is scratch;
# the graded frames belong in output/ next to everything else we deliver.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
ENG="$(cd "$HERE/../.." && pwd)"
REPO="$(cd "$ENG/.." && pwd)"
BIN="$REPO/.micromamba/root/envs/manim/bin"
OUT="$REPO/output/ep001_the_eleven_day_creep"
mkdir -p "$OUT"

names=("StyleFrameA:shot1_ordinary_morning"
       "StyleFrameB:shot2_the_second_look"
       "StyleFrameC:shot3_the_readings"
       "StyleFrameD:end_card_the_question")

for pair in "${names[@]}"; do
  cls="${pair%%:*}"; out="${pair##*:}"
  (cd "$HERE" && "$BIN/python" -m manim -s -qh --disable_caching \
      --media_dir "$ENG/_render" style_frame.py "$cls" > /dev/null 2>&1)
  "$ENG/engine/grade.sh" \
    "$ENG/_render/images/style_frame/${cls}_ManimCE_v0.20.1.png" \
    "$OUT/${out}.png"
  echo "  $OUT/${out}.png"
done
