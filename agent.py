"""
情绪意境海报生成器 · Skill Agent

真正的 Skill 验证方式：
1. 加载 skill/skill.md 作为 Agent 的系统指令
2. 用户输入情绪 → Agent 按 Skill 定义的六步流程执行
3. Agent 生成完整生图 Prompt 后，自动调用万相2.7生成海报

运行：poetry run python agent.py
"""

import os
import re
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
# 加载 Skill 文档
# ─────────────────────────────────────────────

def load_skill() -> str:
    if not SKILL_PATH.exists():
        raise FileNotFoundError(f"Skill 文档未找到：{SKILL_PATH}")
    content = SKILL_PATH.read_text(encoding="utf-8")
    print(f"✅ 已加载 Skill：{SKILL_PATH.name}（{len(content)} 字符）\n")
    return content


# ─────────────────────────────────────────────
# LLM 调用（Qwen-max，作为 Skill 执行引擎）
# ─────────────────────────────────────────────

def call_llm(messages: list[dict], system: str) -> str:
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
    resp = requests.post(LLM_URL, headers=headers, json=payload, timeout=120)
    if not resp.ok:
        print(f"❌ LLM 调用失败：{resp.status_code} {resp.text}")
        return ""
    result = resp.json()
    try:
        return result["output"]["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        print(f"❌ LLM 返回解析失败：{result}")
        return ""


# ─────────────────────────────────────────────
# 从 Agent 回复中提取生图 Prompt
# ─────────────────────────────────────────────

def extract_image_prompt(text: str) -> str | None:
    """
    从 Agent 回复中提取 ```plaintext ... ``` 代码块内的内容
    匹配包含 CRITICAL STYLE REQUIREMENTS 的完整 Prompt
    """
    # 优先匹配 plaintext 代码块
    pattern = r"```(?:plaintext)?\s*(Create a.*?MUST FOLLOW EXACTLY.*?```)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).rstrip("`").strip()

    # 降级：直接匹配 Create a ... 开头的段落
    pattern2 = r"(Create a .+?=== CRITICAL STYLE REQUIREMENTS.*?)(?=\n\n[^-\s]|\Z)"
    match2 = re.search(pattern2, text, re.DOTALL)
    if match2:
        return match2.group(1).strip()

    return None


# ─────────────────────────────────────────────
# 万相2.7 文生图
# ─────────────────────────────────────────────

def generate_image(prompt: str, filename: str) -> Path | None:
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
    print("\n🎨 正在调用万相2.7生成海报...")
    resp = requests.post(IMG_URL, headers=headers, json=payload, timeout=300)
    if not resp.ok:
        print(f"❌ 生图失败：{resp.status_code} {resp.text}")
        return None

    result = resp.json()
    try:
        content = result["output"]["choices"][0]["message"]["content"]
        for item in content:
            if isinstance(item, dict) and "image" in item:
                image_url = item["image"]
                img_resp = requests.get(image_url, timeout=60)
                img_resp.raise_for_status()
                ASSETS_DIR.mkdir(parents=True, exist_ok=True)
                out_path = ASSETS_DIR / filename
                out_path.write_bytes(img_resp.content)
                print(f"💾 已保存：{out_path}")
                return out_path
    except (KeyError, IndexError, TypeError) as e:
        print(f"❌ 解析生图结果失败：{e}")
    return None


# ─────────────────────────────────────────────
# 主 Agent 循环
# ─────────────────────────────────────────────

def run_agent():
    if not DASHSCOPE_API_KEY:
        print("❌ 未找到 DASHSCOPE_API_KEY，请检查 .env 文件")
        return

    # 加载 Skill 作为系统提示
    skill_content = load_skill()

    system_prompt = f"""你是一个严格按照以下 Skill 文档执行的 AI Agent。

Skill 文档内容如下：

{skill_content}

---

执行要求：
1. 严格按照 Skill 定义的六步工作流执行，不可跳过任何步骤
2. 步骤1：主动询问用户的心情，等待用户回复后再进入步骤2
3. 步骤2-4：完成情绪提取、价值提炼、模块拆分（内部处理，不需要全部输出给用户）
4. 步骤5：向用户完整输出「情绪诊断报告」和「完整生图 Prompt」
   - 生图 Prompt 必须用 ```plaintext ... ``` 代码块包裹
   - Prompt 必须是填充了所有变量的实体版本，不能有任何未替换的 {{变量}}
5. 步骤6：询问用户确认后，告知"即将调用万相2.7生成图像"

语言：全程使用中文与用户交流，Prompt 内容保持英文。"""

    messages = []
    image_generated = False

    print("=" * 50)
    print("  情绪意境海报生成器 · Skill Agent")
    print("  输入 quit 退出")
    print("=" * 50)

    while True:
        # ── Agent 主动发起第一句话
        if not messages:
            print("\n🤖 Agent 正在启动...\n")
            # Qwen 要求首条必须是 user，用内部启动指令触发
            messages.append({"role": "user", "content": "[系统启动] 请按照 Skill 文档的步骤1，主动向用户询问心情。"})
            reply = call_llm(messages, system_prompt)
            if not reply:
                break
            # 移除内部启动指令，保持对话干净
            messages.pop()
            messages.append({"role": "assistant", "content": reply})
            print(f"🤖 Agent：{reply}\n")

        # ── 用户输入
        try:
            user_input = input("👤 你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 退出")
            break

        if user_input.lower() in ("quit", "exit", "退出", "q"):
            print("👋 退出")
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        # ── Agent 回复
        print("\n🤖 Agent 思考中...\n")
        reply = call_llm(messages, system_prompt)
        if not reply:
            break
        messages.append({"role": "assistant", "content": reply})
        print(f"🤖 Agent：{reply}\n")

        # ── 检测是否包含完整生图 Prompt，触发生图
        if not image_generated:
            image_prompt = extract_image_prompt(reply)
            if image_prompt:
                print("─" * 50)
                print("📋 检测到完整生图 Prompt，等待你确认后生图")
                print("─" * 50)
                confirm = input("👤 确认生图？(y/n)：").strip().lower()
                if confirm in ("y", "yes", "是", "确认", "好", "ok"):
                    # 从 Prompt 中提取情绪标题作为文件名
                    title_match = re.search(r"Main Emotion Title:\s*(.+)", image_prompt)
                    title = title_match.group(1).strip() if title_match else "output"
                    filename = f"agent-{title}.png"

                    out_path = generate_image(image_prompt, filename)
                    if out_path:
                        print(f"\n✅ 海报生成完成：{out_path}")
                        image_generated = True

                        # 告知 Agent 已生图，进入收尾
                        messages.append({
                            "role": "user",
                            "content": f"图片已生成，保存路径：{out_path}"
                        })
                        closing = call_llm(messages, system_prompt)
                        if closing:
                            messages.append({"role": "assistant", "content": closing})
                            print(f"\n🤖 Agent：{closing}\n")
                else:
                    print("⏸ 已取消生图，你可以继续调整\n")


if __name__ == "__main__":
    run_agent()
