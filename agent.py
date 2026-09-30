"""
海报生成器 · Agent

架构：
  Agent (Qwen-max)
    ← skill/skill.md 作为行为规范
    ← 对话收集情绪（最多2轮追问）
    ↓ Function Calling（仅用于告知 LLM 何时/传什么参数）
  Tool 执行层
    → subprocess 调用 skill/generate_poster.py
    → skill 脚本独立完成 Prompt 组装 + 万相2.7调用
    → 返回图片路径

运行：poetry run python agent.py
"""

import os
import json
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
SKILL_PATH = Path(__file__).parent / "skill" / "skill.md"
SKILL_SCRIPT = Path(__file__).parent / "skill" / "generate_poster.py"

LLM_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


# ─────────────────────────────────────────────
# Function Calling Schema
# 仅用于告知 LLM 收集哪些字段、何时触发
# 实际执行委托给 skill/generate_poster.py
# ─────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "generate_emotion_poster",
            "description": "当你已通过对话收集到足够的情绪信息，调用此工具生成水墨意境海报。",
            "parameters": {
                "type": "object",
                "properties": {
                    "emotion_title":      {"type": "string", "description": "2-4字核心情绪词，如：倦归、虚空、悔"},
                    "surface_emotion":    {"type": "string", "description": "表层情绪：用户明确表达的情绪状态"},
                    "deep_emotion":       {"type": "string", "description": "深层情绪：表层背后真正驱动这种感受的内在状态"},
                    "emotion_imagery":    {"type": "string", "description": "情绪意象：用具体场景描述这种情绪的质感"},
                    "poetic_line":        {"type": "string", "description": "精准匹配的古诗词句"},
                    "poetic_source":      {"type": "string", "description": "诗词出处，如：李白·《春夜洛城闻笛》"},
                    "color_palette":      {"type": "string", "description": "情绪色彩，含 hex 色值，如：深夜藏蓝 #1a2b4a · 孤独感 / 橘灯暖黄 #e8922a · 渴望温暖"},
                    "main_visual_scene":  {"type": "string", "description": "传给万相2.7的英文场景描述，需具体生动"},
                    "annotation_text":    {"type": "string", "description": "情绪注解：1-2行温柔解读"},
                    "heart_voice":        {"type": "string", "description": "用户原话，或你感受到的'他没说出口的话'"},
                    "emotion_tags":       {"type": "string", "description": "#词语格式的情绪标签，如：#倦归 #渴望被看见"},
                    "emotion_timezone":   {"type": "string", "description": "适合在___时刻看这张图，如：深夜归家路上"},
                    "visual_style":       {"type": "string", "enum": ["水墨国画风", "新中式简约风", "古典诗意风"]},
                    "overall_mood":       {"type": "string", "description": "整体氛围英文关键词，如：solitary / nocturnal / yearning"},
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
# Tool 执行：调用 skill/generate_poster.py
# ─────────────────────────────────────────────

def execute_tool(args: dict) -> dict:
    """将参数序列化后通过 subprocess 调用 skill/generate_poster.py"""
    try:
        result = subprocess.run(
            ["python", str(SKILL_SCRIPT)],
            input=json.dumps(args, ensure_ascii=False),
            capture_output=True,
            text=True,
            timeout=360,
            env={**os.environ},
        )
        if result.returncode == 0:
            return json.loads(result.stdout.strip())
        else:
            return {"success": False, "error": result.stderr.strip() or "脚本执行失败"}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "生图超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────
# LLM 调用
# ─────────────────────────────────────────────

def call_llm(messages: list[dict], system: str, use_tools: bool = True) -> dict:
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-max",
        "input": {"system": system, "messages": messages},
        "parameters": {"result_format": "message", "max_tokens": 4096},
    }
    if use_tools:
        payload["parameters"]["tools"] = TOOLS

    resp = requests.post(LLM_URL, headers=headers, json=payload, timeout=120)
    if not resp.ok:
        return {"type": "error", "content": f"LLM 调用失败：{resp.status_code}"}

    try:
        message = resp.json()["output"]["choices"][0]["message"]
        if message.get("tool_calls"):
            tc = message["tool_calls"][0]
            return {
                "type": "tool_call",
                "tool_call_id": tc.get("id", ""),
                "name": tc["function"]["name"],
                "args": json.loads(tc["function"]["arguments"]),
                "raw_message": message,
            }
        return {"type": "text", "content": message.get("content", ""), "raw_message": message}
    except Exception as e:
        return {"type": "error", "content": str(e)}


# ─────────────────────────────────────────────
# Agent Loop
# ─────────────────────────────────────────────

def run_agent():
    if not DASHSCOPE_API_KEY:
        print("❌ 未找到 DASHSCOPE_API_KEY，请检查 .env 文件")
        return

    skill_content = SKILL_PATH.read_text(encoding="utf-8")
    print(f"✅ 已加载 Skill（{len(skill_content)} 字符）\n")

    system_prompt = f"""你是「海报生成器」，通过对话感知用户情绪，生成中式水墨意境海报。

你的完整 Skill 知识如下：
{skill_content}

---

## 行为规范

**开场：** 一句话自我介绍 + 询问用户心情，语气温柔自然。

**收集阶段：**
- 认真倾听，若信息不够则自然追问（最多2轮）
- 不要输出诊断报告，不要输出 Prompt 文本
- 信息足够后，告诉用户「我已经读懂你的心情了，正在为你生成专属海报～」

**触发生图：** 调用 generate_emotion_poster 工具，参数严格按照 Skill 六层诊断框架填充：
- main_visual_scene 等英文字段用英文填写
- emotion_imagery 要具体生动，传达情绪质感
- deep_emotion 要真正挖掘深层，不只是字面重复
- heart_voice 优先用用户原话，没有则生成一句「他没说出口的话」

**语言：** 全程中文与用户交流。"""

    messages = []

    print("=" * 50)
    print("  海报生成器")
    print("  输入 quit 退出")
    print("=" * 50)

    while True:
        # ── 第一轮：Agent 主动开口
        if not messages:
            messages.append({"role": "user", "content": "[启动]"})
            resp = call_llm(messages, system_prompt)
            messages.pop()
            if resp["type"] == "text" and resp["content"]:
                messages.append({"role": "assistant", "content": resp["content"]})
                print(f"\n🤖 {resp['content']}\n")
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
        print("\n🤖 思考中...\n")

        # ── Inner Loop：处理 tool call 链
        while True:
            resp = call_llm(messages, system_prompt)

            if resp["type"] == "error":
                print(f"❌ {resp['content']}")
                break

            elif resp["type"] == "text":
                messages.append({"role": "assistant", "content": resp["content"]})
                print(f"🤖 {resp['content']}\n")
                break

            elif resp["type"] == "tool_call":
                # 记录 tool call 到对话历史
                messages.append({
                    "role": "assistant",
                    "content": resp["raw_message"].get("content") or "",
                    "tool_calls": resp["raw_message"]["tool_calls"],
                })

                print(f"🔧 调用工具：{resp['name']}")
                tool_result = execute_tool(resp["args"])

                # 工具结果返回给 Agent
                messages.append({
                    "role": "tool",
                    "tool_call_id": resp.get("tool_call_id", ""),
                    "name": resp["name"],
                    "content": json.dumps(tool_result, ensure_ascii=False),
                })

                if tool_result["success"]:
                    print(f"✅ 海报已生成：{tool_result['path']}\n")
                else:
                    print(f"❌ 生图失败：{tool_result.get('error')}\n")

                # Agent 收尾语
                closing = call_llm(messages, system_prompt, use_tools=False)
                if closing["type"] == "text" and closing["content"]:
                    messages.append({"role": "assistant", "content": closing["content"]})
                    print(f"🤖 {closing['content']}\n")
                break


if __name__ == "__main__":
    run_agent()
