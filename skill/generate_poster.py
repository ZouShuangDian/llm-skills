#!/usr/bin/env python3
"""
情绪意境海报生成脚本

用法：
  # 方式一：通过 stdin 传入 JSON
  echo '{"emotion_title": "倦归", ...}' | python skill/generate_poster.py

  # 方式二：通过命令行参数传入 JSON 文件
  python skill/generate_poster.py --input emotion.json

  # 方式三：直接在代码中 import 调用
  from skill.generate_poster import run
  result = run(emotion_data)

所需环境变量：
  DASHSCOPE_API_KEY=your-api-key

输入 JSON 字段说明（见 skill.md 六层诊断框架）：
  emotion_title       必填  2-4字核心情绪词
  surface_emotion     必填  表层情绪
  deep_emotion        必填  深层情绪
  emotion_imagery     必填  情绪意象（具体场景描述）
  poetic_line         必填  匹配诗词
  poetic_source       必填  诗词出处
  color_palette       必填  情绪色彩（含 hex 色值）
  main_visual_scene   必填  主视觉英文场景描述（传给万相2.7）
  annotation_text     必填  情绪注解
  heart_voice         必填  心声留白
  emotion_tags        必填  情绪标签（#词语格式）
  emotion_timezone    必填  情绪时区
  visual_style        必填  水墨国画风 / 新中式简约风 / 古典诗意风
  overall_mood        必填  整体氛围英文关键词
  output_dir          可选  图片保存目录，默认 ./assets
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# 自动查找项目根目录的 .env
_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / ".env")

IMG_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"


def build_prompt(d: dict) -> str:
    """按照 Skill 框架将结构化情绪数据组装成完整的万相2.7生图 Prompt"""
    return f"""Create a Chinese ink-wash and neo-Chinese aesthetic emotional poster for Xiaohongshu about the emotion「{d['emotion_title']}」.

=== CRITICAL STYLE REQUIREMENTS (MUST FOLLOW EXACTLY) ===

【OVERALL VISUAL CONCEPT】
- A deeply emotional, poetic, and visually resonant Chinese-aesthetic poster.
- The poster should feel like a page torn from a personal poetry journal, soaked in ink and emotion.
- Not a commercial poster — a personal emotional artifact with artistic weight and quiet depth.
- The image itself carries the emotion: the ink-wash scene, the negative space, and the brushwork all convey the feeling before the viewer reads any text.
- Inspired by Song Dynasty ink paintings, Tang poetry visual aesthetics, and modern neo-Chinese minimalism.

【COLOR SYSTEM】
- Background: aged rice paper texture / soft warm ivory #f5f0e8 — never pure white
- Primary ink color: deep charcoal black #1a1a1a with visible natural brushstroke texture variation
- Color palette: {d['color_palette']}
- Text color: deep ink black #2a2a2a
- No color swatch strip at the bottom — clean ending
- Strictly avoid: neon colors, oversaturated tones, cold clinical whites, plastic renders

【LAYOUT & STRUCTURE】
- Portrait ratio: 3:4, optimized for Xiaohongshu vertical feed
- Top area (40%): {d['main_visual_scene']}
- Upper-middle: emotion title in bold calligraphy — 「{d['emotion_title']}」— centered, dominant weight
- Middle: poetic line in brush script — 「{d['poetic_line']}」— source: {d['poetic_source']}
- Lower: annotation text — 「{d['annotation_text']}」
- Bottom-left: heart voice in handwriting — 「{d['heart_voice']}」
- Bottom-center: 「适合在{d['emotion_timezone']}看这张图」— very small text
- Bottom-right: {d['emotion_tags']} — minimal fine print
- No color swatch strip. Generous negative space throughout.

【GRAPHIC ELEMENTS】
- Ink wash brushwork as primary visual language, visible dry-brush texture
- Calligraphy-style Chinese characters with individual brush strokes
- Scene elements matching emotion imagery: {d['emotion_imagery']}
- Rice paper grain texture across entire background
- Ink bleeding and feathering at brush stroke edges
- No photography, no photorealistic rendering, no 3D, no anime

【MODULE REQUIREMENTS】
- Module 1 [Emotion Title]: 「{d['emotion_title']}」— bold calligraphy, max visual weight
- Module 2 [Poetic Line]: 「{d['poetic_line']}」— brush script, source: {d['poetic_source']}
- Module 3 [Main Visual]: {d['main_visual_scene']} — ink-wash scene, top 40%
- Module 4 [Annotation]: 「{d['annotation_text']}」— Song-style typeface, lower section
- Module 5 [Heart Voice]: 「{d['heart_voice']}」— handwriting, bottom-left
- Module 6 [Emotion Tags]: {d['emotion_tags']} — minimal fine print, bottom-right
- Module 7 [Emotion Timezone]: 「适合在{d['emotion_timezone']}看这张图」— very small, bottom-center

【TYPOGRAPHY STYLE】
- Title: bold classical Chinese calligraphy (行楷), strong ink presence
- Poetic line: light elegant brush script (行书)
- Annotation: fine Song-style typeface, small and quiet
- Heart voice: casual handwriting, slightly irregular baseline
- Tags and timezone: minimal clean sans-serif, very small
- No English text in the visible design area

【WHAT TO AVOID】
- No anime or kawaii aesthetics
- No neon or bright colors
- No corporate or commercial visual language
- No photorealistic faces or figures
- No color swatch strip at bottom
- No pure white background

【CONTENT FOR THIS IMAGE】
Main Emotion Title: {d['emotion_title']}
Surface Emotion: {d['surface_emotion']}
Deep Emotion: {d['deep_emotion']}
Emotion Imagery: {d['emotion_imagery']}
Poetic Line: {d['poetic_line']}
Poetic Source: {d['poetic_source']}
Main Visual Scene: {d['main_visual_scene']}
Annotation Text: {d['annotation_text']}
Heart Voice: {d['heart_voice']}
Color Palette: {d['color_palette']}
Emotion Tags: {d['emotion_tags']}
Emotion Timezone: 适合在{d['emotion_timezone']}看这张图
Overall Mood: {d['overall_mood']}
Visual Style: {d['visual_style']}"""


def run(data: dict) -> dict:
    """
    核心执行函数，供直接 import 调用。
    返回 {"success": bool, "path": str, "error": str}
    """
    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        return {"success": False, "error": "未找到 DASHSCOPE_API_KEY 环境变量"}

    prompt = build_prompt(data)
    title = data.get("emotion_title", "output")
    output_dir = Path(data.get("output_dir", _ROOT / "assets"))

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "wan2.7-image-pro",
        "input": {
            "messages": [{"role": "user", "content": [{"text": prompt}]}]
        },
        "parameters": {
            "size": "768*1024",
            "n": 1,
            "watermark": False,
            "thinking_mode": True,
        }
    }

    resp = requests.post(IMG_URL, headers=headers, json=payload, timeout=300)
    if not resp.ok:
        return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}

    result = resp.json()
    try:
        content = result["output"]["choices"][0]["message"]["content"]
        for item in content:
            if isinstance(item, dict) and "image" in item:
                img_resp = requests.get(item["image"], timeout=60)
                img_resp.raise_for_status()
                output_dir.mkdir(parents=True, exist_ok=True)
                out_path = output_dir / f"{title}.png"
                out_path.write_bytes(img_resp.content)
                return {"success": True, "path": str(out_path), "title": title}
    except (KeyError, IndexError, TypeError) as e:
        return {"success": False, "error": str(e)}

    return {"success": False, "error": "未找到图片URL"}


def main():
    parser = argparse.ArgumentParser(description="情绪意境海报生成脚本")
    parser.add_argument("--input", "-i", type=str, help="情绪数据 JSON 文件路径")
    args = parser.parse_args()

    # 读取输入：优先文件，其次 stdin
    if args.input:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    else:
        data = json.loads(sys.stdin.read())

    result = run(data)

    # 统一输出 JSON 到 stdout，方便调用方解析
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
