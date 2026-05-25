"""小红书文案服务 - 输出Word (.docx)"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_client import chat
from formatters.word import create_doc

SYSTEM_PROMPT = (
    "你是小红书爆款文案写手。根据关键词和风格生成小红书文案。"
    "请以纯JSON格式返回，不要包含markdown代码块，"
    "键为：title(吸睛标题), content(正文300-500字，用emoji点缀), "
    "hashtags(5-8个话题标签数组), comments(3条评论区引导话术数组)"
)


def run():
    print("\n小红书文案生成")
    print("=" * 40)

    keywords = input("请输入产品/话题关键词：").strip()
    print("请选择文案风格：")
    print("  1. 种草  2. 测评  3. 攻略  4. 日常分享")
    style_map = {"1": "种草", "2": "测评", "3": "攻略", "4": "日常分享"}
    choice = input("请输入编号(1-4)：").strip()
    style = style_map.get(choice, "种草")

    user_msg = f"关键词：{keywords}\n风格：{style}"

    print("\n正在生成文案，请稍候...")
    raw = chat(SYSTEM_PROMPT, user_msg)

    data = json.loads(raw)

    sections = [
        {"heading": "标题", "content": data.get("title", "")},
        {"heading": "正文", "content": data.get("content", "")},
        {
            "heading": "话题标签",
            "content": "  ".join(
                f"#{tag}" if not tag.startswith("#") else tag
                for tag in data.get("hashtags", [])
            ),
            "style": "blue",
        },
        {
            "heading": "评论区引导",
            "content": "\n".join(
                f"{i}. {c}"
                for i, c in enumerate(data.get("comments", []), 1)
            ),
            "style": "quote",
        },
    ]

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"小红书文案_{timestamp}.docx"

    path = create_doc(filename, title=data.get("title", "小红书文案"), sections=sections)
    print(f"\n文案已生成：{path}")


if __name__ == "__main__":
    run()
