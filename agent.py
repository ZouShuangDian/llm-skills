"""
情绪意境海报生成器 · Skill Agent

架构设计：
- Agent (Qwen-max)：加载 skill.md 作为行为规范，通过对话收集用户情绪信息
- Tool (generate_emotion_poster)：接收结构化情绪数据，按 Skill 框架组装 Prompt，调用万相2.7生图
- Agent Loop：Agent 判断信息足够时，通过 Function Calling 触发工具，无需用户手动确认

运行：poetry run python agent.py
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
SKILL_PATH = Path(__file__).parent / "skill" / "skill.md"
ASSETS_DIR = Path(__file__).parent / "assets"

LLM_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
IMG_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"


# ─────────────────────────────────────────────
# Tool 定义（Function Calling Schema）
# ─────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_emotion_poster",
            "description": "当你已经收集到足够的情绪信息，可以完成六层情绪诊断时，调用此工具生成水墨意境海报。工具内部会按照 Skill 框架组装完整的生图 Prompt 并调用万相2.7。",
            "parameters": {
                "type": "object",
                "properties": {
                    "emotion_title": {
                        "type": "string",
                        "description": "2-4字核心情绪词，作为海报主标题。例如：倦归、虚空、悔"
                    },
                    "surface_emotion": {
                        "type": "string",
                        "description": "表层情绪：用户明确表达的情绪词或状态描述"
                    },
                    "deep_emotion": {
                        "type": "string",
                        "description": "深层情绪：表层情绪背后真正驱动这种感受的内在状态"
                    },
                    "emotion_imagery": {
                        "type": "string",
                        "description": "情绪意象：用一个具体的自然场景或生活场景描述这种情绪的质感。例如：深夜便利店橘黄灯光打在雨后路面，一个人站在玻璃门外"
                    },
                    "poetic_line": {
                        "type": "string",
                        "description": "匹配的诗词句子，如：此夜曲中闻折柳，何人不起故园情"
                    },
                    "poetic_source": {
                        "type": "string",
                        "description": "诗词出处，如：李白·《春夜洛城闻笛》"
                    },
                    "color_palette": {
                        "type": "string",
                        "description": "情绪色彩方案，3-4个颜色，格式：色名 #hex · 情绪词，用 / 分隔。例如：深夜藏蓝 #1a2b4a · 孤独感 / 橘灯暖黄 #e8922a · 渴望温暖"
                    },
                    "main_visual_scene": {
                        "type": "string",
                        "description": "主视觉场景的英文描述，用于传递给万相2.7。需具体描述场景元素、光线、氛围、构图"
                    },
                    "annotation_text": {
                        "type": "string",
                        "description": "情绪注解：1-2行对情绪的温柔解读，如：不知道为什么想哭，其实是太久没被好好看见了"
                    },
                    "heart_voice": {
                        "type": "string",
                        "description": "心声留白：用户说的原话，或 Skill 基于深层情绪生成的'你可能想说但没说出口的话'"
                    },
                    "emotion_tags": {
                        "type": "string",
                        "description": "2-3个情绪标签，格式：#词语，如：#倦归 #渴望被看见 #深夜情绪"
                    },
                    "emotion_timezone": {
                        "type": "string",
                        "description": "情绪时区：适合在___时刻看这张图，如：深夜归家路上"
                    },
                    "visual_style": {
                        "type": "string",
                        "enum": ["水墨国画风", "新中式简约风", "古典诗意风"],
                        "description": "海报视觉风格"
                    },
                    "overall_mood": {
                        "type": "string",
                        "description": "整体氛围英文关键词，3-5个，如：solitary / nocturnal / yearning"
                    }
                },
                "required": [
                    "emotion_title", "surface_emotion", "deep_emotion",
                    "emotion_imagery", "poetic_line", "poetic_source",
                    "color_palette", "main_visual_scene", "annotation_text",
                    "heart_voice", "emotion_tags", "emotion_timezone",
                    "visual_style", "overall_mood"
                ]
            }
        }
    }
]


# ─────────────────────────────────────────────
# Tool 实现：组装 Prompt + 调用万相2.7
# ─────────────────────────────────────────────

def build_prompt(args: dict) -> str:
    """按照 Skill 框架将结构化情绪数据组装成完整的万相2.7生图 Prompt"""
    return f"""Create a Chinese ink-wash and neo-Chinese aesthetic emotional poster for Xiaohongshu about the emotion「{args['emotion_title']}」.

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
- Color palette: {args['color_palette']}
- Text color: deep ink black #2a2a2a with slight brush texture variation between strokes
- No color swatch strip at the bottom — clean ending
- Strictly avoid: neon colors, oversaturated tones, cold clinical whites, plastic or digital-looking renders

【LAYOUT & STRUCTURE】
- Portrait ratio: 3:4, optimized for Xiaohongshu vertical feed
- Top area (40% of height): {args['main_visual_scene']}
- Upper-middle area: emotion title in bold calligraphy — 「{args['emotion_title']}」— dominant visual weight, centered
- Middle area: poetic line in lighter brush script — 「{args['poetic_line']}」— with source credit — {args['poetic_source']}
- Lower area: annotation text — 「{args['annotation_text']}」— quiet and unhurried
- Bottom-left corner: heart voice in casual handwriting — 「{args['heart_voice']}」
- Bottom-center: very small text — 「适合在{args['emotion_timezone']}看这张图」
- Bottom-right corner: emotion tags {args['emotion_tags']} in very small minimal fine print
- No color swatch strip — clean ending
- Negative space: generous throughout

【GRAPHIC ELEMENTS】
- Ink wash brushwork as primary visual language, with visible dry-brush texture
- Calligraphy-style Chinese characters with individual visible brush strokes and ink density variation
- Nature and scene elements matching the emotion imagery: {args['emotion_imagery']}
- Subtle rice paper grain texture across the entire background surface
- Ink bleeding and feathering effects at the edges of brush strokes
- No photography, no photorealistic rendering, no 3D elements, no anime influences

【MODULE REQUIREMENTS】
- Module 1 [Emotion Title]: 「{args['emotion_title']}」— bold calligraphy, maximum visual weight
- Module 2 [Poetic Line]: 「{args['poetic_line']}」— brush script, source: {args['poetic_source']}
- Module 3 [Main Visual]: {args['main_visual_scene']} — ink-wash scene, top 40%
- Module 4 [Annotation]: 「{args['annotation_text']}」— Song-style typeface, lower section
- Module 5 [Heart Voice]: 「{args['heart_voice']}」— handwriting, bottom-left corner
- Module 6 [Emotion Tags]: {args['emotion_tags']} — minimal fine print, bottom-right
- Module 7 [Emotion Timezone]: 「适合在{args['emotion_timezone']}看这张图」— very small text, bottom-center

【TYPOGRAPHY STYLE】
- Primary title: bold classical Chinese calligraphy (行楷), strong ink presence
- Poetic line: light elegant brush script (行书), flowing and unhurried
- Annotation text: fine Song-style typeface, small and quiet
- Heart voice: casual handwriting, slightly irregular baseline, intimate
- Emotion timezone and tags: minimal clean sans-serif, very small, unobtrusive
- No English text in the visible design area

【WHAT TO AVOID】
- No anime or kawaii aesthetic influences
- No bright rainbow colors or neon palette
- No corporate or commercial poster visual language
- No photorealistic human faces or figures
- No color swatch strip at bottom
- No pure white #ffffff background

【CONTENT FOR THIS IMAGE】
Main Emotion Title: {args['emotion_title']}
Surface Emotion: {args['surface_emotion']}
Deep Emotion: {args['deep_emotion']}
Poetic Line: {args['poetic_line']}
Poetic Line Source: {args['poetic_source']}
Main Visual Scene: {args['main_visual_scene']}
Annotation Text: {args['annotation_text']}
Heart Voice: {args['heart_voice']}
Color Palette: {args['color_palette']}
Emotion Tags: {args['emotion_tags']}
Emotion Timezone: 适合在{args['emotion_timezone']}看这张图
Overall Mood Keywords: {args['overall_mood']}
Visual Style: {args['visual_style']}"""


def generate_emotion_poster(args: dict) -> dict:
    """Tool 实现：组装 Prompt 并调用万相2.7生图"""
    prompt = build_prompt(args)
    title = args.get("emotion_title", "output")

    print(f"\n🎨 正在为「{title}」生成专属海报...")

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
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
                image_url = item["image"]
                img_resp = requests.get(image_url, timeout=60)
                img_resp.raise_for_status()
                ASSETS_DIR.mkdir(parents=True, exist_ok=True)
                out_path = ASSETS_DIR / f"agent-{title}.png"
                out_path.write_bytes(img_resp.content)
                return {"success": True, "path": str(out_path), "title": title}
    except (KeyError, IndexError, TypeError) as e:
        return {"success": False, "error": str(e)}

    return {"success": False, "error": "未找到图片URL"}


# ─────────────────────────────────────────────
# LLM 调用（支持 Function Calling）
# ─────────────────────────────────────────────

def call_llm(messages: list[dict], system: str, use_tools: bool = True) -> dict:
    """返回 {"type": "text"|"tool_call", "content": str | {"name": str, "args": dict}}"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-max",
        "input": {
            "system": system,
            "messages": messages,
        },
        "parameters": {
            "result_format": "message",
            "max_tokens": 4096,
        }
    }
    if use_tools:
        payload["parameters"]["tools"] = TOOLS

    resp = requests.post(LLM_URL, headers=headers, json=payload, timeout=120)
    if not resp.ok:
        print(f"❌ LLM 调用失败：{resp.status_code} {resp.text}")
        return {"type": "error", "content": ""}

    result = resp.json()
    try:
        message = result["output"]["choices"][0]["message"]
        # Function Call
        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            return {
                "type": "tool_call",
                "tool_call_id": tool_call.get("id", ""),
                "name": tool_call["function"]["name"],
                "args": json.loads(tool_call["function"]["arguments"]),
                "raw_message": message,
            }
        # 普通文本回复
        return {
            "type": "text",
            "content": message.get("content", ""),
            "raw_message": message,
        }
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"❌ 解析失败：{e}")
        return {"type": "error", "content": ""}


# ─────────────────────────────────────────────
# 主 Agent Loop
# ─────────────────────────────────────────────

def load_skill() -> str:
    content = SKILL_PATH.read_text(encoding="utf-8")
    print(f"✅ 已加载 Skill：{SKILL_PATH.name}（{len(content)} 字符）\n")
    return content


def run_agent():
    if not DASHSCOPE_API_KEY:
        print("❌ 未找到 DASHSCOPE_API_KEY，请检查 .env 文件")
        return

    skill_content = load_skill()

    system_prompt = f"""你是「情绪意境海报生成器」，专门通过对话收集用户情绪，然后生成中式水墨意境海报。

你拥有的完整 Skill 知识如下：
{skill_content}

---

## 行为规范

**启动：** 简短自我介绍，问用户现在心情怎么样。语气温柔自然，像朋友。

**对话收集阶段：**
- 认真倾听用户说的每一句话
- 如果信息不够完成情绪诊断（太短/太模糊），自然追问1-2个问题
- 最多追问 2 轮，之后无论如何进入生图阶段
- **不要列出诊断报告给用户看，不要输出 Prompt 文本**

**触发生图：**
- 当情绪信息足够时，告诉用户「我已经读懂你的心情了，正在为你生成专属海报～」
- 然后立即调用 generate_emotion_poster 工具，将收集到的所有情绪信息作为参数传入
- 工具调用的参数必须严格按照 Skill 文档中的六层诊断框架填充：
  - emotion_title：从情绪中提炼的2-4字标题
  - deep_emotion：不只是字面情绪，要挖掘深层
  - emotion_imagery：用具体场景描述情绪质感
  - poetic_line / poetic_source：精准匹配的古诗词
  - color_palette：含 hex 色值的情绪色彩
  - main_visual_scene：传给万相2.7的英文场景描述，要具体生动
  - annotation_text：温柔的情绪解读
  - heart_voice：用户说的话，或你感受到的「他没说出口的话」
  - emotion_timezone：「适合在___时刻看」的场景描述

**语言：** 全程中文与用户交流。工具参数按要求填写（main_visual_scene 等字段用英文）。"""

    messages = []

    print("=" * 50)
    print("  情绪意境海报生成器")
    print("  输入 quit 退出")
    print("=" * 50)

    # Agent Loop
    while True:
        # ── 第一轮：Agent 主动开口
        if not messages:
            messages.append({
                "role": "user",
                "content": "[系统启动] 开始对话"
            })
            response = call_llm(messages, system_prompt)
            if response["type"] == "error":
                break

            messages.pop()  # 移除启动指令

            if response["type"] == "text":
                messages.append({"role": "assistant", "content": response["content"]})
                print(f"\n🤖 {response['content']}\n")
                continue

        # ── 等待用户输入
        try:
            user_input = input("👤 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见")
            break

        if user_input.lower() in ("quit", "exit", "退出", "q"):
            print("👋 再见")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        # ── Agent 思考 + 可能触发工具
        print("\n🤖 思考中...\n")

        while True:
            response = call_llm(messages, system_prompt)

            if response["type"] == "error":
                break

            elif response["type"] == "text":
                # 普通对话回复，继续收集信息
                messages.append({"role": "assistant", "content": response["content"]})
                print(f"🤖 {response['content']}\n")
                break

            elif response["type"] == "tool_call":
                # Agent 决定调用工具生图
                tool_name = response["name"]
                tool_args = response["args"]

                # 把工具调用记录进对话历史
                messages.append({
                    "role": "assistant",
                    "content": response["raw_message"].get("content") or "",
                    "tool_calls": response["raw_message"]["tool_calls"],
                })

                if tool_name == "generate_emotion_poster":
                    result = generate_emotion_poster(tool_args)

                    # 把工具结果返回给 Agent
                    messages.append({
                        "role": "tool",
                        "tool_call_id": response.get("tool_call_id", ""),
                        "name": tool_name,
                        "content": json.dumps(result, ensure_ascii=False),
                    })

                    if result["success"]:
                        print(f"✅ 海报已生成：{result['path']}\n")
                    else:
                        print(f"❌ 生图失败：{result.get('error')}\n")

                    # Agent 根据工具结果生成收尾语
                    closing = call_llm(messages, system_prompt, use_tools=False)
                    if closing["type"] == "text" and closing["content"]:
                        messages.append({"role": "assistant", "content": closing["content"]})
                        print(f"🤖 {closing['content']}\n")
                    break


if __name__ == "__main__":
    run_agent()
