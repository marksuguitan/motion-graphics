#!/bin/bash
# usage: ./stills.sh 3 7.8 ...   (VO seconds)
mkdir -p out/st
for t in "$@"; do fr=$(python3 -c "print(round(($t+1.5+2.2)*30))"); npx remotion still build SVT out/st/t$t.png --frame=$fr --log=error & done; wait
