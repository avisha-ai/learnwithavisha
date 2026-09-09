#!/bin/bash
# LearnWithAvisha — Visual Pilot 001 finishing grade.
#   bloom   soft glow on the warm rims and the dawn, the way a real lens
#           behaves against a low sun
#   vignette pulls the eye off the frame edges
#   grain   unifies the flat vector fills into one image
# Usage: ./grade.sh in.(png|mp4) out.(png|mp4)
set -e
FF="/Users/mrinalgala/Documents/Avisha/learnwithavisha/.micromamba/root/envs/manim/bin/ffmpeg"
CHAIN="split[a][b];[b]gblur=sigma=20[c];[a][c]blend=all_mode=screen:all_opacity=0.105,\
eq=contrast=1.07:saturation=0.99,\
vignette=angle=PI/6.2,\
noise=alls=6:allf=t+u"
case "$2" in
  *.png) "$FF" -v error -i "$1" -vf "$CHAIN" -y "$2" ;;
  *) "$FF" -v error -i "$1" -vf "$CHAIN" -r 60 -c:v libx264 -preset slow \
       -crf 17 -pix_fmt yuv420p -movflags +faststart -y "$2" ;;
esac
