#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建底图：base_00.png（红字卡）+ base_01..10.png（插画，去水印）。
用法: python3 build_bases.py <config.json>
去水印方法：裁掉源图底边（水印最高到 y1086），crop((0,20,2048,1075))，等比放大铺满。
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 2880, 2160
TOP_H = 279          # 顶栏 + 分隔线1
IMG_Y = 280
IMG_H = 1562
BOT_Y = 1842
RED = (234, 26, 26)
SRC_CROP = (0, 20, 2048, 1075)   # 裁掉底部水印


def main():
    cfg = json.load(open(sys.argv[1]))
    work = cfg["work_dir"]
    build = os.path.join(work, "build")
    os.makedirs(build, exist_ok=True)
    font = cfg.get("font_path", os.path.join(work, "fonts", "NotoSansSC-VF.ttf"))
    hook = cfg["hook_text"]
    ill_dir = cfg["illustrations_dir"]
    pattern = cfg.get("illustration_pattern", "豆包 ({idx}).png")
    n = cfg.get("n_illustrations", len(cfg["copy"]))   # 插画数可多于文案数（末尾 outro 用）

    chrome_top = Image.open(os.path.join(build, "chrome_top.png")).convert("RGB")
    chrome_bot = Image.open(os.path.join(build, "chrome_bottom.png")).convert("RGB")

    def composite(area_rgb):
        """把插画区贴到顶栏+底带之间。"""
        canvas = Image.new("RGB", (W, H), (255, 255, 255))
        canvas.paste(chrome_top, (0, 0))
        canvas.paste(area_rgb, (0, IMG_Y))
        canvas.paste(chrome_bot, (0, BOT_Y))
        return canvas

    # ---- base_00: 红字卡 ----
    area = Image.new("RGB", (W, IMG_H), (255, 255, 255))
    f = ImageFont.truetype(font, 294)
    try:
        f.set_variation_by_axes([800])
    except Exception:
        pass
    d = ImageDraw.Draw(area)
    bbox = d.textbbox((0, 0), hook, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((W - tw) // 2 - bbox[0], (IMG_H - th) // 2 - bbox[1]), hook, font=f, fill=RED)
    composite(area).save(os.path.join(build, "base_00.png"))

    # ---- base_01..N: 插画 ----
    for idx in range(1, n + 1):
        src = Image.open(os.path.join(ill_dir, pattern.format(idx=idx))).convert("RGB")
        c = src.crop(SRC_CROP)
        scale = IMG_H / c.height
        c2 = c.resize((int(round(c.width * scale)), IMG_H), Image.LANCZOS)
        x = (c2.width - W) // 2
        area = c2.crop((x, 0, x + W, IMG_H))
        composite(area).save(os.path.join(build, f"base_{idx:02d}.png"))

    print(f"bases done: base_00..base_{n:02d}.png ({n+1} files)")


if __name__ == "__main__":
    main()
