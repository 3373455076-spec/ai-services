"""日程规划 → Excel (.xlsx)"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_client import chat
from formatters.excel import create_schedule_excel

SYSTEM_PROMPT = (
    "你是时间管理专家。根据用户的待办事项、可用时间和优先级偏好，生成合理的日程安排。"
    "请以纯JSON格式返回，不要包含markdown代码块，不要包含任何额外文字，"
    "键为：schedule(数组，每项含time_slot(时间段如09:00-10:30), task(任务名), "
    "duration(预估时长), priority(高/中/低), notes(备注/提醒)), "
    "tips(2条效率提升建议数组)"
)

HEADERS = ["时间段", "任务", "预估时长", "优先级", "备注"]


def run():
    print("\n日程规划")
    print("=" * 40)

    todo_items = input("请输入待办事项（多项用逗号分隔）：").strip()
    time_slots = input("请输入可用时间段（如 09:00-12:00, 14:00-18:00）：").strip()
    priorities = input("请输入优先级偏好（如：先做重要紧急的任务）：").strip()

    user_prompt = (
        f"待办事项：{todo_items}\n"
        f"可用时间段：{time_slots}\n"
        f"优先级偏好：{priorities}"
    )

    print("\n正在生成日程安排，请稍候...")
    raw = chat(SYSTEM_PROMPT, user_prompt)
    data = json.loads(raw)

    ts = int(time.time())

    # Build rows from schedule data
    rows = []
    for item in data["schedule"]:
        rows.append([
            item["time_slot"],
            item["task"],
            item["duration"],
            item["priority"],
            item["notes"],
        ])

    tips = data.get("tips", [])

    filename = f"日程规划_{ts}.xlsx"
    path = create_schedule_excel(
        filename=filename,
        title="日程安排",
        headers=HEADERS,
        rows=rows,
        tips=tips,
    )

    print(f"\n日程规划已生成：{path}")
    print("\n--- 日程安排 ---")
    for item in data["schedule"]:
        print(f"  {item['time_slot']}  {item['task']}  [{item['priority']}]  {item['notes']}")
    if tips:
        print("\n--- 效率建议 ---")
        for i, tip in enumerate(tips, 1):
            print(f"  {i}. {tip}")


if __name__ == "__main__":
    run()
