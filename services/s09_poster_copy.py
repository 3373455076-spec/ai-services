"""海报文案撰写 → PNG image + TXT"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_client import chat
from formatters.image import create_poster
from config import OUTPUT_DIR

SYSTEM_PROMPT = (
    "你是活动策划与文案专家。根据活动信息生成海报文案和推广文案。"
    "请以纯JSON格式返回，不要包含markdown代码块，不要包含任何额外文字，"
    "键为：main_title(海报主标题，6字以内), subtitle(副标题), "
    "poster_body(海报正文150字以内), long_copy(推文版文案300-500字), "
    "moments_copies(3条朋友圈转发短文案数组), "
    "event_info(活动时间地点等信息，用换行分隔)"
)


def run():
    print("\n海报文案撰写")
    print("=" * 40)

    event_name = input("请输入活动名称：").strip()
    time_location = input("请输入活动时间和地点：").strip()
    audience = input("请输入目标受众：").strip()
    selling_point = input("请输入核心卖点：").strip()
    style = input("请选择风格（正式/活泼/文艺）：").strip()

    user_prompt = (
        f"活动名称：{event_name}\n"
        f"时间和地点：{time_location}\n"
        f"目标受众：{audience}\n"
        f"核心卖点：{selling_point}\n"
        f"风格：{style}"
    )

    print("\n正在生成海报文案，请稍候...")
    raw = chat(SYSTEM_PROMPT, user_prompt)
    data = json.loads(raw)

    ts = int(time.time())

    # Generate poster image
    png_filename = f"海报_{ts}.png"
    png_path = create_poster(
        filename=png_filename,
        main_title=data["main_title"],
        subtitle=data["subtitle"],
        body_text=data["poster_body"],
        event_info=data["event_info"],
    )

    # Generate companion text file with long_copy and moments_copies
    txt_filename = f"海报文案_{ts}.txt"
    txt_path = os.path.join(OUTPUT_DIR, txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("【推文版文案】\n")
        f.write("=" * 40 + "\n")
        f.write(data["long_copy"] + "\n\n")
        f.write("【朋友圈转发短文案】\n")
        f.write("=" * 40 + "\n")
        for i, copy in enumerate(data["moments_copies"], 1):
            f.write(f"{i}. {copy}\n\n")

    print(f"\n海报已生成：{png_path}")
    print(f"文案已保存：{txt_path}")
    print("\n--- 海报主标题 ---")
    print(data["main_title"])
    print("\n--- 副标题 ---")
    print(data["subtitle"])
    print("\n--- 推文版文案（节选） ---")
    print(data["long_copy"][:100] + "...")
    print("\n--- 朋友圈短文案 ---")
    for i, copy in enumerate(data["moments_copies"], 1):
        print(f"  {i}. {copy}")


if __name__ == "__main__":
    run()
