---
name: 牛马觉醒日记
description: 制作「牛马觉醒日记」系列抖音短视频（4:3 / 2880×2160 / 30fps）。输入：一期插画文件夹（右下角带 AI 水印）、一条参考成片（用于提取配乐、配音音色、版式）、文案列表、期号标题。输出：成片 mp4 + 封面 jpg。当用户说"做一期牛马觉醒日记视频""按第八期风格做新一期""用这些插画做短视频"等时使用。
---

# 牛马觉醒日记系列视频制作

端到端流程：插画 → 配音 → 字幕对齐 → 逐帧渲染 → 混音 → 编码。所有脚本在 `scripts/`，版式常量在 `references/layout.md`，时间轴设计方法在 `references/timeline.md`。

## 工作目录约定

每期建一个工作目录（如 `work/`），内含：
- `build/` — 底图、帧序列（`build/frames/f_%05d.jpg`）
- `audio/` — 配音、配乐、混音
- `fonts/` — 思源黑体可变字体（见下方"字体"）

## 流程

### 1. 收集输入

- 插画文件夹：10 张 2048×1152 PNG，右下角带「豆包AI生成」水印
- 参考成片：mp4，用于提取配乐（BGM）和配音音色样本
- 文案：开场 hook（如"永远记住一句话"）+ 期号标题 + N 条正文（每条对应一张插画）
- 输出路径与文件名

### 2. 从参考成片提取配乐与人声样本

用 mediakit `audio separate-voice` 分离参考视频的 BGM 和人声，得到 `bgm_ref.wav`、`voice_ref.wav`。`voice_ref.wav` 用作配音音色参考（A2A）。

### 3. 生成配音（A2A）

用 `audio_to_audio_plus`，参考音色填 `voice_ref.wav` 的 URL。**prompt 必须写"一口气连贯播报、句子之间只做很短的换气停顿、不要出现超过一秒的静音空档"**——否则生成的配音停顿极不均匀。配音文本 = hook + 期号标题句 + 正文逐条。

生成后用 mediakit `video asr-subtitles` 跑 ASR，拿到逐句起止时间（JSON，`subtitles[].start_time / end_time / subtitle_text`）。**这是字幕对齐的唯一权威依据**，不要凭配音总时长均分。

### 4. 设计镜头与字幕时间轴

读 `references/timeline.md`。核心规则：
- 开场期号标题句**只配音不出字幕**，第一帧红字卡保持不动直到第一条正文配音开始
- 每条字幕窗口 = `[配音起 − 0.22s, 配音止 + 0.38s]`
- 镜头切换点对齐字幕切换点（每张插画对应一条正文）
- 末两句若配音是一口气读完，合并为一条字幕

### 5. 构建顶栏与字幕带（chrome）

```bash
python3 scripts/build_chrome.py <config.json>
```

输出 `build/chrome_top.png`（2880×280）和 `build/chrome_bottom.png`（2880×318）。顶栏含抖音 logo、期号标题（思源黑体 w800）、"个人观点，仅供参考"（思源黑体 w500）。

### 6. 构建底图（红字卡 + 10 张插画，去水印）

```bash
python3 scripts/build_bases.py <config.json>
```

输出 `build/base_00.png`（红字卡）~ `base_10.png`。

**去水印方法（关键）**：插画源图右下角水印最高到 y1086，直接裁掉底边 `crop((0, 20, 2048, 1075))` 再等比放大铺满插画区（2880×1562）。**不要用 inpainting/扩散修补**——线稿交叠处会留灰色残影。

### 7. 逐帧渲染（字幕 + 叠化）

```bash
python3 scripts/render_frames.py <config.json>
```

输出 `build/frames/f_00001.jpg` ~。叠化 12 帧（0.4s），只作用于插画区（y280–1842），顶栏与字幕带硬切。字幕首尾各 5 帧淡入淡出。

### 8. 混音与编码

```bash
bash scripts/finalize.sh <config.json>
```

- 配乐裁到成片时长 + 1.5s 片尾淡出
- 配音补到等长
- 混音：配乐 `volume=0.5dB`（比人声响约 2.5 LU，按参考实测校准）
- loudnorm 两遍：目标 I=−18.4 LUFS、TP=−0.5 dBFS
- 编码：libx264 crf17、yuv420p limited bt709、AAC 192k、`+faststart`
- 封面：取红字卡稳定帧（约 2.0s）

## 配置文件

所有脚本读同一个 JSON config。字段：

```json
{
  "work_dir": "/abs/path/to/work",
  "episode_title": "职场小白注意！上班禁区千万别碰，踩一个都容易吃亏",
  "hook_text": "永远记住一句话",
  "copy": ["别迟到出头", "别跟同事掏心窝聊是非", "..."],
  "illustrations_dir": "/abs/path/to/第九期",
  "illustration_pattern": "豆包 ({idx}).png",
  "n_illustrations": 10,
  "voice_wav": "/abs/path/to/audio/voice_raw.wav",
  "bgm_wav": "/abs/path/to/audio/bgm_ref.wav",
  "shot_t": [0.0, 9.05, 11.2, "..."],
  "sub_win": [[0.34, 2.40, "永远记住一句话"], "..."],
  "duration": 35.5,
  "output_mp4": "/abs/path/to/牛马觉醒日记09-上班禁区.mp4",
  "output_cover": "/abs/path/to/牛马觉醒日记09-上班禁区-封面.jpg"
}
```

`shot_t` 和 `sub_win` 由第 4 步生成后填入。

## 内置示例（第九期）

- `assets/episode09/` — 第九期 10 张原始插画（带 AI 水印，作为去水印流程的输入样例和格式参考）
- `references/episode09_config.json` — 第九期完整 config（文案、shot_t、sub_win 全部填好），可直接复制后改 `work_dir` / `voice_wav` / `bgm_wav` / 输出路径跑通全流程
- 新一期做 config 时，以此为模板改 `episode_title` / `hook_text` / `copy` / `illustrations_dir`，`shot_t` / `sub_win` 按新一期配音 ASR 重新生成

## 字体

思源黑体可变字体 `NotoSansSC-VF.ttf`（Weight 轴 100–900）。若本地没有，从 `https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf` 下载到 `fonts/`。

**关键**：PIL 加载后必须 `font.set_variation_by_axes([weight])` 才生效，否则永远是默认细体。标题 w800、注脚 w500、字幕 w800。

## 关键坑（踩过的）

1. **字幕串台**：`faded()` 的淡出缓存键只用了透明度量化值，两个不同字幕图层出现相同 alpha 时会复用对方的已淡出掩码。修法：缓存键改为 `(id(layer), key)`。
2. **配音不连贯**：不写"一口气连贯播报"的 prompt 时，生成的配音句间停顿可达 3–4 秒且漏句。
3. **水印修补残影**：用扩散/修补去水印，线稿交叠处留灰色多边形残影。裁底边是最干净的方案。
4. **ffmpeg**：本机无系统 ffmpeg，用 `python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"` 取路径。
5. **响度**：直接混音后必须跑两遍 loudnorm（先测后校），否则响度不达标。
6. **字幕对齐**：按镜头均分字幕会导致中后段与配音漂移 0.5–1.0 秒。必须用 ASR 逐句时间。

## 交付前校验

- 回抽成片关键帧（开场红字卡、每条正文起/止、片尾）目视确认字幕与插画正确
- `ffmpeg -i out.mp4 -af ebur128=peak=true -f null -` 确认 I≈−18.4、TP≤−1.5
- 确认无水印残留、无字幕串台、叠化平滑
