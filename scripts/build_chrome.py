#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建顶栏与字幕带（chrome）。
用法: python3 build_chrome.py <config.json>
输出: <work_dir>/build/chrome_top.png (2880x280), chrome_bottom.png (2880x318)
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

W = 2880
TOP_H = 266          # 顶栏高
SEP1 = 13             # 分隔线1高
BAND_H = 303          # 字幕带高
SEP2 = 15             # 分隔线2高
INK = (17, 17, 17)
NOTE_INK = (150, 142, 145)
BG = (249, 249, 249)
SEP = (3, 3, 3)
LOGO_POS = (58, 40)
TITLE_BOX = (240, 117, 1930, 82)   # x, y, w, h
NOTE_BOX = (2215, 124, 538, 61)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)


def load_font(path, weight):
    f = ImageFont.truetype(path, 200)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def ink_size(font, text):
    """返回文字渲染后的实际 ink 宽高（像素）。"""
    tmp = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def render_ink_box(font_path, text, weight, box_w, box_h, color):
    """二分搜索字号使 ink 宽 ≈ box_w，直接渲染（不缩放），返回 RGBA 图。"""
    lo, hi = 10, 500
    best = None
    for _ in range(40):
        mid = (lo + hi) // 2
        f = ImageFont.truetype(font_path, mid)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        iw, ih = ink_size(f, text)
        if iw < box_w:
            best = (mid, iw, ih)
            lo = mid + 1
        else:
            hi = mid - 1
    size, iw, ih = best or (200, box_w, box_h)
    f = ImageFont.truetype(font_path, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    pad = 20
    canvas = Image.new("RGBA", (iw + pad * 2, ih + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    d.text((pad, pad), text, font=f, fill=color + (255,))
    bbox = canvas.getbbox()
    return canvas.crop(bbox)


def main():
    cfg = json.load(open(sys.argv[1]))
    work = cfg["work_dir"]
    build = os.path.join(work, "build")
    os.makedirs(build, exist_ok=True)
    font = cfg.get("font_path", os.path.join(work, "fonts", "NotoSansSC-VF.ttf"))
    title = cfg["episode_title"]
    note = cfg.get("note_text", "个人观点，仅供参考")

    # ---- 顶栏 ----
    top = Image.new("RGB", (W, TOP_H + SEP1), BG)
    d = ImageDraw.Draw(top)
    d.rectangle([0, TOP_H, W, TOP_H + SEP1], fill=SEP)
    logo_path = os.path.join(SKILL_DIR, "assets", "douyin_logo.png")
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        top.paste(logo, LOGO_POS, logo)
    ti = render_ink_box(font, title, 800, TITLE_BOX[2], TITLE_BOX[3], INK)
    top.paste(ti, (TITLE_BOX[0], TITLE_BOX[1]), ti)
    ni = render_ink_box(font, note, 500, NOTE_BOX[2], NOTE_BOX[3], NOTE_INK)
    top.paste(ni, (NOTE_BOX[0], NOTE_BOX[1]), ni)
    top.save(os.path.join(build, "chrome_top.png"))

    # ---- 字幕带 ----
    bot = Image.new("RGB", (W, SEP2 + BAND_H), BG)
    d = ImageDraw.Draw(bot)
    d.rectangle([0, 0, W, SEP2], fill=SEP)
    bot.save(os.path.join(build, "chrome_bottom.png"))
    print(f"chrome done: chrome_top.png ({top.size}), chrome_bottom.png ({bot.size})")


if __name__ == "__main__":
    main()
