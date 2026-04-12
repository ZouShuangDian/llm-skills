#!/usr/bin/env python3
"""
情绪意境海报生成脚本

用法：
    python scripts/generate.py --prompt "完整的生图Prompt文本" [--size 768*1024] [--output ./output]

所需环境变量：
    DASHSCOPE_API_KEY=your-api-key

参数：
    --prompt    必填  完整的万相2.7生图 Prompt（由 SKILL.md 中的框架生成）
    --size      可选  图片尺寸，默认 768*1024（3:4竖版，适配小红书）
    --output    可选  图片保存目录，默认 ./output
    --n         可选  生成数量，默认 1
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    # 向上查找 .env 文件
    for parent in [Path(__file__).parent, Path(__file__).parent.parent, Path(__file__).parent.parent.parent]:
        env_file = parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            break
except ImportError:
    pass

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
IMG_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"


def generate(prompt: str, size: str = "768*1024", n: int = 1, output_dir: str = "./output") -> list[str]:
    """
    调用万相2.7文生图接口生成图片。

    Args:
        prompt:     完整的生图 Prompt
        size:       图片尺寸，如 768*1024 / 1024*1024 / 2K
        n:          生成数量
        output_dir: 图片保存目录

    Returns:
        保存的图片路径列表
    """
    if not API_KEY:
        print("错误：未找到 DASHSCOPE_API_KEY 环境变量", file=sys.stderr)
        print("请参考 references/common.md 配置 API Key", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "wan2.7-image-pro",
        "input": {
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ]
        },
        "parameters": {
            "size": size,
            "n": n,
            "watermark": False,
            "thinking_mode": True,
        }
    }

    print(f"正在调用万相2.7（wan2.7-image-pro）生成图片，尺寸：{size}，数量：{n}...")
    resp = requests.post(IMG_URL, headers=headers, json=payload, timeout=300)

    if not resp.ok:
        print(f"错误：API 调用失败 {resp.status_code} - {resp.text}", file=sys.stderr)
        sys.exit(1)

    result = resp.json()
    saved_paths = []

    try:
        content = result["output"]["choices"][0]["message"]["content"]
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, item in enumerate(content):
            if isinstance(item, dict) and "image" in item:
                img_resp = requests.get(item["image"], timeout=60)
                img_resp.raise_for_status()
                filename = f"poster_{timestamp}_{i+1}.png"
                out_file = output_path / filename
                out_file.write_bytes(img_resp.content)
                saved_paths.append(str(out_file))
                print(f"图片已保存：{out_file}")

    except (KeyError, IndexError, TypeError) as e:
        print(f"错误：解析API返回结果失败 - {e}", file=sys.stderr)
        sys.exit(1)

    if not saved_paths:
        print("错误：未获取到图片", file=sys.stderr)
        sys.exit(1)

    return saved_paths


def main():
    parser = argparse.ArgumentParser(
        description="情绪意境海报生成脚本 - 调用万相2.7（wan2.7-image-pro）生成水墨意境海报",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python scripts/generate.py --prompt "Create a Chinese ink-wash poster..."
  python scripts/generate.py --prompt "..." --size 1024*1024 --output ./my_posters
  python scripts/generate.py --prompt "..." --n 2

所需环境变量：
  DASHSCOPE_API_KEY=your-api-key  （参考 references/common.md）
        """
    )
    parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="完整的万相2.7生图 Prompt（由 SKILL.md 框架生成）"
    )
    parser.add_argument(
        "--size", "-s",
        default="768*1024",
        help="图片尺寸，默认 768*1024（3:4竖版适配小红书）。可选：1024*1024 / 2K 等"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="生成数量，默认 1"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="图片保存目录，默认 ./output"
    )

    args = parser.parse_args()
    paths = generate(args.prompt, args.size, args.n, args.output)

    print(f"\n完成！共生成 {len(paths)} 张图片：")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
