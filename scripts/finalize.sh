#!/usr/bin/env bash
# 混音（BGM + 配音，两遍 loudnorm 到 -18.4 LUFS）+ 编码成片 + 生成封面。
# 用法: bash finalize.sh <config.json>
set -euo pipefail
CFG="$1"

read_json() { python3 -c "import json,sys; d=json.load(open('$CFG')); print(d$1)"; }

WORK=$(read_json '["work_dir"]')
BUILD="$WORK/build"
FRAMES="$BUILD/frames"
AUDIO="$WORK/audio"
DUR=$(read_json '["duration"]')
VOICE=$(read_json '["voice_wav"]')
BGM=$(read_json '["bgm_wav"]')
OUT_MP4=$(read_json '["output_mp4"]')
OUT_COVER=$(read_json '["output_cover"]')

FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p "$AUDIO"

echo "[1/5] 裁配乐 + 配音补长"
FADE_START=$(python3 -c "print(round($DUR - 1.5, 2))")
"$FF" -y -hide_banner -loglevel error -i "$BGM" \
  -af "atrim=0:${DUR},afade=t=out:st=${FADE_START}:d=1.50" \
  "$AUDIO/bgm_trim.wav"
"$FF" -y -hide_banner -loglevel error -i "$VOICE" \
  -af "apad=whole_dur=${DUR}" "$AUDIO/voice_pad.wav"

echo "[2/5] 混音（配乐比人声响约 2.5 LU）"
"$FF" -y -hide_banner -loglevel error \
  -i "$AUDIO/voice_pad.wav" -i "$AUDIO/bgm_trim.wav" \
  -filter_complex "[1:a]volume=0.5dB[b];[0:a][b]amix=inputs=2:duration=longest:normalize=0" \
  "$AUDIO/mix_raw.wav"

echo "[3/5] loudnorm 第一遍（测量）"
LN=$("$FF" -hide_banner -i "$AUDIO/mix_raw.wav" \
  -af "loudnorm=I=-18.4:TP=-0.5:LRA=11:print_format=json" -f null - 2>&1 | python3 -c "
import sys,json
t=sys.stdin.read()
j=json.loads(t[t.index('{'):])
print(f\"measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}\")
")
echo "    $LN"

echo "[4/5] loudnorm 第二遍（线性校正）+ 编码成片"
"$FF" -y -hide_banner -loglevel warning \
  -framerate 30 -i "$FRAMES/f_%05d.jpg" \
  -i "$AUDIO/mix_raw.wav" \
  -map 0:v -map 1:a \
  -af "loudnorm=I=-18.4:TP=-0.5:LRA=11:${LN}:linear=true" \
  -vf "scale=in_range=full:out_range=limited,format=yuv420p" \
  -c:v libx264 -preset medium -crf 17 \
  -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  -r 30 -c:a aac -b:a 192k -ar 44100 -shortest -movflags +faststart \
  "$OUT_MP4"

echo "[5/5] 生成封面（取 2.0s 红字卡帧）"
"$FF" -y -hide_banner -loglevel error -ss 2.0 -i "$OUT_MP4" -frames:v 1 \
  -q:v 2 "$OUT_COVER"

echo "done: $OUT_MP4"
echo "      $OUT_COVER"
