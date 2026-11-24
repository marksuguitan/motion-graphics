#!/usr/bin/env bash
# make_audio.sh: writes public/short9-<id>.vo.mp3 (VO only; make_beeps.py then writes the final short9-<id>.mp3) for Shorts 2, 3 and 5 from the main VO (public/vo.mp3, take B, 1.5 s lead-in).
# Each = 3.7 s of silence (logo intro 2.2 s + hook 1.5 s), the VO stretch a..b (VO seconds, as in src/ShortsV9.tsx), 8.6 s of silence for the outro.
set -euo pipefail
cd "$(dirname "$0")/public"
for x in "narrow 8.6 36.85" "reason 39.3 73.35" "tells 95.15 126.95"; do
  set -- $x
  d=$(python3 -c "print(round($3-$2,3))"); s=$(python3 -c "print($2+1.5)"); fo=$(python3 -c "print($3-$2-0.03)")
  ffmpeg -v error -y -ss "$s" -t "$d" -i vo.mp3 -af "aresample=48000,afade=t=in:d=0.02,afade=t=out:st=$fo:d=0.03,adelay=3700:all=1,apad=pad_dur=8.6" -ac 1 -b:a 192k "short9-$1.vo.mp3"
done
