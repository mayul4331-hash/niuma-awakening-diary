# 牛马觉醒日记

「牛马觉醒日记」系列抖音短视频的端到端制作工具。输入一期火柴人插画 + 参考成片 + 文案，自动输出 4:3 竖版短视频（2880×2160 / 30fps）。

## 这是什么

把「插画 → 配音 → 字幕对齐 → 逐帧渲染 → 混音 → 编码」整条流水线固化成可复用脚本，每期只换插画和文案，就能复现同一套版式、配乐、配音音色。

**已内置第九期完整示例**：10 张原始插画 + 完整配置文件，改几个路径即可跑通全流程。

## 输出规格

| 项目 | 规格 |
|---|---|
| 画幅 | 4:3，2880×2160，30fps |
| 编码 | H.264 (libx264, crf 17) + AAC 192k，yuv420p bt709 |
| 响度 | −18.4 LUFS（抖音合规） |
| 版式 | 顶栏（抖音 logo + 期号标题 + 免责声明）+ 插画区 + 底部字幕带 |
| 特效 | 插画间 0.4s 叠化转场，字幕淡入淡出 |
| 水印 | 自动去除插画右下角「豆包AI生成」水印 |

## 目录结构

```
.
├── SKILL.md                  # 给 AI Agent 的完整使用说明
├── README.md                 # 本文件（人类阅读）
├── scripts/
│   ├── build_chrome.py       # 构建顶栏与字幕带底图
│   ├── build_bases.py        # 构建红字卡 + 插画底图（去水印）
│   ├── render_frames.py      # 逐帧渲染（字幕 + 叠化）
│   └── finalize.sh           # 混音 + 编码 + 封面
├── references/
│   ├── layout.md             # 版式常量（坐标、字号、颜色）
│   ├── timeline.md           # 时间轴设计方法
│   └── episode09_config.json # 第九期完整配置（可直接用）
└── assets/
    ├── douyin_logo.png       # 抖音 logo（透明底）
    └── episode09/            # 第九期 10 张原始插画
```

## 使用方式

### 前置依赖

- Python 3 + Pillow + numpy
- ffmpeg（可用 `imageio_ffmpeg` 自带的二进制）
- 思源黑体可变字体 `NotoSansSC-VF.ttf`

### 快速开始（用第九期示例跑通）

```bash
# 1. 建工作目录
mkdir -p work/{build,audio,fonts}
cd work

# 2. 下载思源黑体（若本地没有）
curl -L -o fonts/NotoSansSC-VF.ttf \
  "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf"

# 3. 复制第九期配置，把里面的绝对路径改成你自己的
cp ../references/episode09_config.json config.json
# 编辑 config.json：修改 work_dir / voice_wav / bgm_wav / output_mp4 / output_cover

# 4. 依次跑四个脚本
python3 ../scripts/build_chrome.py  config.json   # 顶栏 + 字幕带
python3 ../scripts/build_bases.py   config.json   # 红字卡 + 插画底图（去水印）
python3 ../scripts/render_frames.py config.json   # 逐帧渲染
bash  ../scripts/finalize.sh        config.json   # 混音 + 编码 + 封面
```

成片和封面输出到 `config.json` 里指定的路径。

### 做新一期

1. 准备新一期 10 张插画（2048×1152 PNG，右下角带水印）
2. 用一条参考成片提取配乐和配音音色（`mediakit audio separate-voice`）
3. 用 `audio_to_audio_plus` 生成配音——**prompt 必须写「一口气连贯播报、句间只做很短换气停顿、不要超过一秒静音」**，否则停顿极不均匀且漏句
4. 对配音跑 ASR，拿到逐句起止时间（字幕对齐的唯一权威依据，不要按镜头均分）
5. 以 `references/episode09_config.json` 为模板，改 `episode_title` / `hook_text` / `copy` / `illustrations_dir`，填入新的 `shot_t` / `sub_win`
6. 跑上面四个脚本

详细的时间轴设计、版式参数、踩坑记录见 [`SKILL.md`](SKILL.md) 和 [`references/`](references/)。

## 关键设计决策

- **去水印用裁切，不用 inpainting**：线稿交叠处扩散修补会留灰色残影，裁掉底边最干净
- **字幕按 ASR 逐句对齐，不按镜头均分**：均分导致中后段漂移 0.5–1.0 秒
- **配音 prompt 强制「一口气连贯播报」**：否则句间停顿 3–4 秒且漏句
- **叠化只作用插画区**：顶栏和字幕带硬切，避免文字抖动
- **loudnorm 两遍**：先测后校，保证 −18.4 LUFS

## 交付前自检

- 回抽关键帧（开场红字卡、每条正文起/止、片尾）目视确认字幕与插画
- `ffmpeg -i out.mp4 -af ebur128=peak=true -f null -` 确认 I≈−18.4、TP≤−1.5
- 确认无水印残留、无字幕串台、叠化平滑

## 许可

个人创作工具，插画素材为示例用途。
