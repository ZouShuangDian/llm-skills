"""
万相2.7 情绪意境海报生成脚本
生成3个不同情绪示例，用于 skill.md 效果对比展示

运行：poetry run python generate_demo.py
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
ASSETS_DIR = Path(__file__).parent / "assets"

# ─────────────────────────────────────────────
# 示例1：倦归 · 深夜孤独
# 输入：今天又加班到很晚，回家路上看到便利店还亮着灯，突然很想哭，也不知道为什么
# ─────────────────────────────────────────────
PROMPT_1 = """Create a Chinese ink-wash and neo-Chinese aesthetic emotional poster for Xiaohongshu about the emotion「倦归」.

=== CRITICAL STYLE REQUIREMENTS (MUST FOLLOW EXACTLY) ===

【OVERALL VISUAL CONCEPT】
- A deeply emotional, poetic, and visually resonant Chinese-aesthetic poster.
- The poster should feel like a page torn from a personal poetry journal, soaked in ink and emotion.
- Not a commercial poster — a personal emotional artifact with artistic weight and quiet depth.
- The image itself carries the emotion: the ink-wash scene, the negative space, and the brushwork all work together to convey the feeling before the viewer reads any text.
- Inspired by Song Dynasty ink paintings, Tang poetry visual aesthetics, and modern neo-Chinese minimalism.

【COLOR SYSTEM】
- Background: aged rice paper texture / soft warm ivory #f5f0e8 — never pure white
- Primary ink color: deep charcoal black #1a1a1a with visible natural brushstroke texture variation
- Emotional accent color: 橘灯暖黄 #e8922a — applied to the convenience store light glow and emotion title
- Secondary emotional color: 深夜藏蓝 #1a2b4a — used in the night sky atmosphere and shadow areas
- Tertiary color: 湿路灰黑 #2c2c2c — wet pavement reflection and mid-tone ink wash
- No color swatch strip at the bottom — clean ending

【LAYOUT & STRUCTURE】
- Portrait ratio: 3:4, optimized for Xiaohongshu vertical feed
- Top area (40% of height): deep night street scene — a lone convenience store glowing warm amber in blue-black ink-wash darkness, rain-wet pavement reflecting the light, viewed from outside looking in, one solitary figure standing at the edge of the light
- Upper-middle area: emotion title in bold calligraphy — 「倦归」— dominant visual weight, centered
- Middle area: poetic line in lighter brush script — 「此夜曲中闻折柳，何人不起故园情」— positioned below title with breathing space
- Lower area: annotation text — 「不知道为什么想哭，其实是太久没被好好看见了」— quiet and unhurried
- Bottom-left corner: user's original words in casual handwriting — 「回家路上看到便利店还亮着灯，突然很想哭」
- Bottom-center: very small text — 「适合在深夜归家路上看这张图」
- Bottom-right corner: emotion tags #倦归 #渴望被看见 #深夜情绪 in very small minimal fine print
- Negative space: generous throughout

【GRAPHIC ELEMENTS】
- Ink wash brushwork as primary visual language: night sky rendered in deep indigo-black wash, building silhouettes as loose ink shapes
- Convenience store: warm amber light spilling out through glass windows rendered as ink-wash light bloom, not photorealistic
- Rain-wet pavement: horizontal ink wash strokes with light reflection suggesting wetness
- Solitary figure: minimal ink silhouette, viewed from behind, small against the scene
- Calligraphy title characters with individual visible brush strokes and slight ink density variation
- Rice paper grain texture across entire background
- No photography, no photorealistic rendering, no 3D elements, no anime influences

【MODULE REQUIREMENTS】
- Module 1 [Emotion Title]: 「倦归」— 2 bold calligraphy characters, maximum visual weight
- Module 2 [Poetic Line]: 「此夜曲中闻折柳，何人不起故园情」— brush script, source: 李白·《春夜洛城闻笛》
- Module 3 [Main Visual]: deep night convenience store scene with lone figure outside in the rain, ink-wash style
- Module 4 [Annotation]: 「不知道为什么想哭，其实是太久没被好好看见了」— Song-style typeface, lower section
- Module 5 [Heart Voice]: 「回家路上看到便利店还亮着灯，突然很想哭」— handwriting in bottom-left corner
- Module 6 [Emotion Tags]: #倦归 #渴望被看见 #深夜情绪 — minimal fine print at bottom-right
- Module 7 [Emotion Timezone]: 「适合在深夜归家路上看这张图」— very small text at bottom-center

【TYPOGRAPHY STYLE】
- Primary title: bold classical Chinese calligraphy (行楷), strong ink presence
- Poetic line: light elegant brush script (行书), flowing and unhurried
- Annotation text: fine Song-style typeface, small and quiet
- User voice: casual handwriting, slightly irregular baseline, intimate
- No English text in the visible design area

【WHAT TO AVOID】
- No anime or kawaii aesthetic influences
- No bright rainbow colors or neon palette
- No corporate or commercial poster visual language
- No photorealistic human faces or figures
- No color swatch strip at bottom
- No pure white #ffffff background

【CONTENT FOR THIS IMAGE】
Main Emotion Title: 倦归
Poetic Line: 此夜曲中闻折柳，何人不起故园情
Poetic Line Source: 李白·《春夜洛城闻笛》
Main Visual Scene: A lone convenience store glowing warm amber in deep blue-black night, rain-wet pavement reflecting the orange light, a solitary ink-silhouette figure standing outside the glass door looking in, viewed from behind, rendered entirely in ink-wash style
Annotation Text: 不知道为什么想哭，其实是太久没被好好看见了
User Voice: 回家路上看到便利店还亮着灯，突然很想哭
Emotion Tags: #倦归 #渴望被看见 #深夜情绪
Emotion Timezone: 适合在深夜归家路上看这张图
Overall Mood Keywords: solitary / nocturnal / yearning / ink-soaked / quietly devastated
Visual Style: 水墨国画风"""

# ─────────────────────────────────────────────
# 示例2：虚空 · 完成后的空
# 输入：今天终于做完了一件拖了很久的事，有点空
# ─────────────────────────────────────────────
PROMPT_2 = """Create a Chinese ink-wash and neo-Chinese aesthetic emotional poster for Xiaohongshu about the emotion「虚空」.

=== CRITICAL STYLE REQUIREMENTS (MUST FOLLOW EXACTLY) ===

【OVERALL VISUAL CONCEPT】
- A quietly contemplative, minimalist Chinese ink-wash poster.
- The poster should feel like the stillness after a long rain has stopped — empty, clean, and unexpectedly peaceful.
- Not melancholic, not joyful — the specific feeling of completing something and not knowing what comes next.
- Maximum negative space. Emptiness is the subject.
- Inspired by the zen emptiness of late Tang landscape paintings and Japanese ma (間) philosophy applied to Chinese aesthetics.

【COLOR SYSTEM】
- Background: very light warm gray #ede9e0 / pale rice paper — luminous but not white
- Primary ink color: soft charcoal #3a3a3a — lighter than usual, as if the ink has dried slowly
- Emotional accent color: 晨雾青 #a8bfb0 — a muted celadon used sparingly on distant mountains or a tea cup
- Secondary color: 淡墨灰 #c8c4bc — for mid-ground elements and atmospheric wash
- Highlight: a faint warm glow #f0e8d5 — the single window catching afternoon light
- No color swatch strip — clean minimal ending

【LAYOUT & STRUCTURE】
- Portrait ratio: 3:4, optimized for Xiaohongshu vertical feed
- Top area (35% of height): a sparse ink-wash scene — an empty room interior, a window with afternoon light coming through, a tea cup on a windowsill, simple ink strokes for floorboards, a sense of stillness after activity
- Upper-middle area: emotion title in medium-weight calligraphy — 「虚空」— not as heavy as grief, lighter than before
- Middle area: poetic line in light brush script — 「行到水穷处，坐看云起时」
- Lower area: annotation text — 「做完了，却不知道接下来该做什么，这种空也是一种完成」
- Bottom-left corner: user's words in casual handwriting — 「终于做完了，有点空」
- Bottom-right corner: emotion tags #虚空 #完成之后 #静下来了 in very small minimal fine print
- Generous negative space — at least 40% of the composition should be empty paper

【GRAPHIC ELEMENTS】
- Extremely minimal ink-wash scene: empty room, single window, afternoon light as a soft warm wash
- Tea cup or small object on windowsill — single focal point, rendered with a few careful strokes
- Faint ink suggestion of floorboards or floor texture
- Soft atmospheric celadon wash for distant sky visible through window
- Rice paper grain texture throughout
- No busy scene — restraint is the visual language
- No photography, no photorealistic rendering, no anime influences

【MODULE REQUIREMENTS】
- Module 1 [Emotion Title]: 「虚空」— medium-weight calligraphy, quieter than usual
- Module 2 [Poetic Line]: 「行到水穷处，坐看云起时」— brush script, source: 王维·《终南别业》
- Module 3 [Main Visual]: empty room with window light, minimal ink-wash, maximum negative space
- Module 4 [Annotation]: 「做完了，却不知道接下来该做什么，这种空也是一种完成」
- Module 5 [Heart Voice]: 「终于做完了，有点空」— casual handwriting, bottom-left
- Module 6 [Emotion Tags]: #虚空 #完成之后 #静下来了 — minimal fine print, bottom-right
- Module 7 [Emotion Timezone]: 「适合在一个人坐着发呆时看这张图」— very small text at bottom-center

【TYPOGRAPHY STYLE】
- Primary title: medium-weight classical calligraphy — not heavy, as if written quietly
- Poetic line: very light brush script, minimal ink, unhurried
- Annotation text: fine Song-style typeface, small, reflective tone
- User voice: casual handwriting, bottom-left, small and unassuming
- No English text in the visible design area

【WHAT TO AVOID】
- No heavy or dramatic ink brushwork
- No busy or crowded scenes
- No bright or saturated colors
- No corporate or commercial feel
- No color swatch strip at bottom
- No pure white background

【CONTENT FOR THIS IMAGE】
Main Emotion Title: 虚空
Poetic Line: 行到水穷处，坐看云起时
Poetic Line Source: 王维·《终南别业》
Main Visual Scene: An empty, quiet room interior with soft afternoon light coming through a simple window, a tea cup on the sill, minimal ink strokes, vast empty paper space suggesting stillness after completion
Annotation Text: 做完了，却不知道接下来该做什么，这种空也是一种完成
User Voice: 终于做完了，有点空
Emotion Tags: #虚空 #完成之后 #静下来了
Emotion Timezone: 适合在一个人坐着发呆时看这张图
Overall Mood Keywords: empty / still / post-completion / quietly contemplative / zen
Visual Style: 新中式简约风"""

# ─────────────────────────────────────────────
# 示例3：悔 · 说错话后的焦灼
# 输入：和朋友吵架了，说了不该说的话
# ─────────────────────────────────────────────
PROMPT_3 = """Create a Chinese ink-wash and neo-Chinese aesthetic emotional poster for Xiaohongshu about the emotion「悔」.

=== CRITICAL STYLE REQUIREMENTS (MUST FOLLOW EXACTLY) ===

【OVERALL VISUAL CONCEPT】
- A restless, burning, and deeply human Chinese ink-wash poster.
- The poster should feel like the moment after words have left your mouth and you cannot take them back.
- Warm dark tones, like dying embers — the heat of regret, not the cold of grief.
- The ink itself should feel agitated — less controlled, more emotional brushwork.
- Inspired by expressive Song Dynasty ink paintings and the emotional intensity of ci poetry (宋词).

【COLOR SYSTEM】
- Background: aged warm paper #f0e6d8 — slightly warmer than usual, almost like firelight
- Primary ink color: deep ink black #1a1a1a with more agitated, less controlled brushstrokes
- Emotional accent color: 深秋赭红 #8b3a2a — used on fallen leaves, the emotion title, and key emotional elements
- Secondary color: 枯叶棕 #7a5230 — for fallen leaves and dried ink textures
- Tertiary color: 冷灰 #8a8a8a — for the empty path ahead, the distance
- No color swatch strip — clean ending

【LAYOUT & STRUCTURE】
- Portrait ratio: 3:4, optimized for Xiaohongshu vertical feed
- Top area (40% of height): a deep autumn path scene — fallen leaves covering a stone path, a figure's back disappearing into ink-wash mist in the distance, the path continuing forward but the figure growing small, rendered in expressive ink with red-brown leaf accents
- Upper-middle area: single character emotion title in bold calligraphy — 「悔」— heavy, slightly imperfect brushwork suggesting emotional urgency
- Middle area: poetic line — 「林花谢了春红，太匆匆」— brush script
- Lower area: annotation text — 「话说出去的那一刻，就知道不对了，可是来不及了」
- Bottom-left corner: user's words in handwriting — 「说了不该说的话」
- Bottom-right corner: emotion tags #悔 #来不及了 #说错了话 in very small minimal fine print
- Negative space in the upper distance — the mist swallowing the path ahead

【GRAPHIC ELEMENTS】
- Autumn path in ink-wash: stone path with fallen leaves in red-brown ink accent, rendered with more expressive brushwork
- Distant figure: small ink silhouette walking away, back turned, disappearing into mist
- Fallen leaves: a few loose ink-and-color brushstrokes in 深秋赭红, scattered on the path
- Ink mist: soft wash obscuring the distance, suggesting irreversibility
- More agitated ink texture than usual — this emotion has energy, not just stillness
- Rice paper grain throughout
- No photography, no photorealistic rendering, no anime

【MODULE REQUIREMENTS】
- Module 1 [Emotion Title]: 「悔」— single bold character, heavy ink, slightly urgent brushwork
- Module 2 [Poetic Line]: 「林花谢了春红，太匆匆」— brush script, source: 李煜·《乌夜啼》
- Module 3 [Main Visual]: deep autumn path with fallen leaves, distant figure walking away into ink mist
- Module 4 [Annotation]: 「话说出去的那一刻，就知道不对了，可是来不及了」
- Module 5 [Heart Voice]: 「说了不该说的话」— handwriting, bottom-left
- Module 6 [Emotion Tags]: #悔 #来不及了 #说错了话 — minimal fine print, bottom-right
- Module 7 [Emotion Timezone]: 「适合在深夜一个人后悔时看这张图」— very small text at bottom-center

【TYPOGRAPHY STYLE】
- Primary title 悔: single bold character, heavy ink, slight roughness in the brushstroke suggesting emotional agitation
- Poetic line: brush script, slightly more urgent rhythm than the other examples
- Annotation text: fine Song-style typeface, small, honest tone
- User voice: casual handwriting, bottom-left
- No English text in the visible design area

【WHAT TO AVOID】
- No overly decorative or ornamental style
- No cold or blue-toned palette — this emotion is warm and burning
- No corporate or commercial feel
- No photorealistic human faces
- No color swatch strip at bottom
- No pure white background

【CONTENT FOR THIS IMAGE】
Main Emotion Title: 悔
Poetic Line: 林花谢了春红，太匆匆
Poetic Line Source: 李煜·《乌夜啼》
Main Visual Scene: A deep autumn stone path covered in fallen leaves rendered in red-brown ink accents, a small solitary figure walking away into ink-wash mist in the distance, back turned, disappearing — the path continues but the moment cannot be recalled
Annotation Text: 话说出去的那一刻，就知道不对了，可是来不及了
User Voice: 说了不该说的话
Emotion Tags: #悔 #来不及了 #说错了话
Emotion Timezone: 适合在深夜一个人后悔时看这张图
Overall Mood Keywords: regret / burning / autumnal / irreversible / restless
Visual Style: 古典诗意风"""


EXAMPLES = [
    {"name": "demo-倦归", "prompt": PROMPT_1},
    {"name": "demo-虚空", "prompt": PROMPT_2},
    {"name": "demo-悔",   "prompt": PROMPT_3},
]


def call_api(prompt: str) -> str | None:
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
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

    resp = requests.post(url, headers=headers, json=payload, timeout=300)
    if not resp.ok:
        print(f"  ❌ HTTP {resp.status_code}：{resp.text}")
        return None

    result = resp.json()
    try:
        content = result["output"]["choices"][0]["message"]["content"]
        for item in content:
            if isinstance(item, dict) and "image" in item:
                return item["image"]
    except (KeyError, IndexError, TypeError) as e:
        print(f"  ❌ 解析失败：{e}\n  完整返回：{json.dumps(result, ensure_ascii=False)[:300]}")
    return None


def download(url: str, path: Path):
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)


def main():
    if not API_KEY:
        print("❌ 未设置 DASHSCOPE_API_KEY，请检查 .env 文件")
        return

    for example in EXAMPLES:
        name = example["name"]
        print(f"\n{'─'*40}")
        print(f"🎨 生成：{name}")
        image_url = call_api(example["prompt"])
        if not image_url:
            print(f"  ⚠️ 跳过 {name}")
            continue
        out_path = ASSETS_DIR / f"{name}.png"
        download(image_url, out_path)
        print(f"  ✅ 已保存：{out_path}")

    print(f"\n{'─'*40}")
    print("🏁 全部完成")


if __name__ == "__main__":
    main()
