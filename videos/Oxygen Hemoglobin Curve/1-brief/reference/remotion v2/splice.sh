#!/bin/bash
# usage: splice.sh <main30.mp4> <out.mp4>
# Renders the logo dash (1.1–1.97 s) at 480 fps, averages 16 sub-frames per output frame
# (360° shutter motion blur, as in the square→triangle study) and splices it into the 30 fps render.
set -e
npx remotion render src/index.ts MainHi out/hi.mp4 --frames=528-959 --concurrency=4 --crf=10 --muted --log=error
ffmpeg -y -v error -i out/hi.mp4 -vf "tmix=frames=16,select='not(mod(n\,16))',setpts=N/30/TB" -r 30 -c:v libx264 -crf 12 -pix_fmt yuv420p out/hi30.mp4
# hi30 frame j = output frame 33+j (j=0 is partly blurred from missing history; use j>=1 → frames 34..59)
ffmpeg -y -v error -i "$1" -i out/hi30.mp4 -filter_complex \
 "[0:v]trim=start_frame=0:end_frame=34,setpts=PTS-STARTPTS[a];[1:v]trim=start_frame=1:end_frame=27,setpts=PTS-STARTPTS[b];[0:v]trim=start_frame=60,setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
 -map "[v]" -map 0:a -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart "$2"
