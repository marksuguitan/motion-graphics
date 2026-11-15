#!/usr/bin/env bash
# splice.sh: cuts the two Kardiograph plugs into the finished v8 and writes v9.
#   scripts/splice.sh <v8.mp4> <opener.mp4> <endplug.mp4> <out.mp4>
# v8 = svt-vs-sinus-tach-final-draft.mp4 from the YouTube package on Mark's Mac (2:57.7, 30 fps, 48 kHz).
# Render the plugs first: npx remotion render Opener opener.mp4 / npx remotion render EndPlug endplug.mp4
#
#   v8 frames 0-370       (to the title card, in the VO pause 11.91-12.43 s)
#   Opener frames 1-278   (frame 0 is v8 frame 370 itself)
#   v8 frames 371-5095    (to the blank paper before the Subscribe card, v8 frames 5091-5100 are blank)
#   EndPlug frames 0-644  (starts and ends on the same blank paper)
#   v8 frames 5096-end
# Each piece is encoded on its own (one filter graph over the whole video ran out of memory), then joined.
set -euo pipefail
V8=$1; OP=$2; EP=$3; OUT=$4
TMP=$(mktemp -d)
E=(-c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p -r 30 -c:a aac -b:a 192k -ar 48000 -ac 2)
SPF=1600 # audio samples per frame at 48 kHz, 30 fps
ffmpeg -v error -y -i "$V8" -vf "trim=end_frame=371,setpts=PTS-STARTPTS" -af "atrim=end_sample=$((371*SPF)),asetpts=PTS-STARTPTS" "${E[@]}" "$TMP/a.mp4"
ffmpeg -v error -y -i "$OP" -vf "trim=start_frame=1,setpts=PTS-STARTPTS" -af "aresample=48000,apad,atrim=start_sample=$SPF:end_sample=$((279*SPF)),asetpts=PTS-STARTPTS" "${E[@]}" "$TMP/p.mp4"
ffmpeg -v error -y -i "$V8" -vf "trim=start_frame=371:end_frame=5096,setpts=PTS-STARTPTS" -af "atrim=start_sample=$((371*SPF)):end_sample=$((5096*SPF)),asetpts=PTS-STARTPTS" "${E[@]}" "$TMP/b1.mp4"
N=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$EP" | tr -d ,)
ffmpeg -v error -y -i "$EP" -vf "setpts=PTS-STARTPTS" -af "aresample=48000,apad,atrim=end_sample=$((N*SPF)),asetpts=PTS-STARTPTS" "${E[@]}" "$TMP/e.mp4"
ffmpeg -v error -y -i "$V8" -vf "trim=start_frame=5096,setpts=PTS-STARTPTS" -af "atrim=start_sample=$((5096*SPF)),asetpts=PTS-STARTPTS" "${E[@]}" "$TMP/b2.mp4"
printf "file %s\n" "$TMP/a.mp4" "$TMP/p.mp4" "$TMP/b1.mp4" "$TMP/e.mp4" "$TMP/b2.mp4" > "$TMP/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
