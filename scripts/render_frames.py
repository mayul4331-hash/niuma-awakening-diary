#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐帧渲染：字幕（按配音时间轴）+ 镜头叠化。
用法: python3 render_frames.py <config.json>
输出: <work_dir>/build/frames/f_%05d.jpg
关键: faded() 缓存键必须含图层身份 id(layer)，否则不同字幕会串台复用淡出掩码。
"""
import json, os, sys, shutil
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 2880, 2160, 30
IMG_Y = 280
IMG_H = 1562
SUB_CY = 2026
SUB_CX = 1440
BASE_FS = 122
MAX_W = 2640
FADE = 5          # 字幕首尾淡入淡出帧数
DISS = 12         # 叠化帧数（0.4s），只作用插画区

_fade_cache = {}


def faded(layer, factor):
    """按 factor (0~1) 调整图层 alpha，带缓存。缓存键含图层身份以防串台。"""
    key = (id(layer), round(factor * 20))
    if key in _fade_cache:
        return _fade_cache[key]
    if factor >= 0.999:
        out = layer
    else:
        a = layer.split()[3].point(lambda v: int(v * factor))
        out = layer.copy()
        out.putalpha(a)
    _fade_cache[key] = out
    return out


def sub_layer(text, font_path):
    """渲染一条字幕为 RGBA 图层（居中，字号自适应不超过 MAX_W）。"""
    size = BASE_FS
    f = ImageFont.truetype(font_path, size)
    try:
        f.set_variation_by_axes([800])
    except Exception:
        pass
    tmp = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    while tw > MAX_W and size > 40:
        size -= 2
        f = ImageFont.truetype(font_path, size)
        try:
            f.set_variation_by_axes([800])
        except Exception:
            pass
        bbox = d.textbbox((0, 0), text, font=f)
        tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad = 30
    layer = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((pad - bbox[0], pad - bbox[1]), text, font=f, fill=(17, 17, 17, 255))
    return layer


def main():
    cfg = json.load(open(sys.argv[1]))
    work = cfg["work_dir"]
    build = os.path.join(work, "build")
    frames_dir = os.path.join(build, "frames")
    if os.path.exists(frames_dir):
        shutil.rmtree(frames_dir)
    os.makedirs(frames_dir)
    font = cfg.get("font_path", os.path.join(work, "fonts", "NotoSansSC-VF.ttf"))
    duration = cfg.get("duration", 35.5)
    shot_t = cfg["shot_t"]
    sub_win = cfg["sub_win"]
    n_shots = len(shot_t) - 1

    def F(t):
        return int(round(t * FPS))

    shot_frames = [F(t) for t in shot_t]
    total = F(duration)

    # 叠化窗口：(lo, hi, prev_shot, next_shot)
    diss_wins = []
    for k in range(1, n_shots):
        b = shot_frames[k]
        diss_wins.append((b - DISS // 2, b + DISS // 2, k - 1, k))

    # 预渲染所有字幕图层
    sub_layers = [sub_layer(t, font) for _, _, t in sub_win]

    # 预加载所有底图的插画区（用于叠化）
    illus = []
    for s in range(n_shots):
        base = Image.open(os.path.join(build, f"base_{s:02d}.png")).convert("RGB")
        illus.append(base.crop((0, IMG_Y, W, IMG_Y + IMG_H)))

    for i in range(1, total + 1):
        # 确定当前镜头
        shot = 0
        for k in range(n_shots):
            if i >= shot_frames[k] and i < shot_frames[k + 1]:
                shot = k
                break
        base = Image.open(os.path.join(build, f"base_{shot:02d}.png")).convert("RGB")

        # 叠化
        for lo, hi, kp, kn in diss_wins:
            if lo <= i < hi:
                factor = (i - lo) / DISS
                blended = Image.blend(illus[kp], illus[kn], factor)
                base.paste(blended, (0, IMG_Y))
                break

        # 字幕
        for si, (s, e, _) in enumerate(sub_win):
            sf, ef = F(s), F(e)
            if sf <= i < ef:
                if i - sf < FADE:
                    factor = (i - sf) / FADE
                elif ef - i < FADE:
                    factor = (ef - i) / FADE
                else:
                    factor = 1.0
                layer = faded(sub_layers[si], factor)
                lx = SUB_CX - layer.width // 2
                ly = SUB_CY - layer.height // 2
                base.paste(layer, (lx, ly), layer)
                break

        base.save(os.path.join(frames_dir, f"f_{i:05d}.jpg"), quality=92, subsampling=0)

    print(f"frames done: {total} frames @ {FPS}fps = {total/FPS:.1f}s")


if __name__ == "__main__":
    main()
