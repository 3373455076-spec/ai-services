import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_client import chat
from formatters.word import create_doc


SYSTEM = (
    "你是PPT内容策划专家。根据主题、用途和页数生成完整的PPT逐页内容文稿。"
    "请以纯JSON格式返回，不要包含markdown代码块，"
    "键为：title(演示标题), pages(数组，每项含page_num, page_title, "
    "bullet_points(要点数组), speaker_notes(演讲备注))"
)


def run():
    print("\n【PPT 大纲 + 逐页内容生成】")
    print("=" * 40)

    topic = input("请输入演示主题: ").strip()
    print("用途场景: 1.课堂汇报  2.工作述职  3.产品介绍")
    scene_map = {"1": "课堂汇报", "2": "工作述职", "3": "产品介绍"}
    scene_choice = input("请选择 (1/2/3): ").strip()
    scene = scene_map.get(scene_choice, scene_choice)
    page_count = input("期望页数 (10-20，默认15): ").strip() or "15"

    user_msg = (
        f"主题：{topic}\n用途场景：{scene}\n期望页数：{page_count}\n"
        "请生成完整的PPT逐页内容文稿。"
    )

    print("\n正在生成 PPT 大纲，请稍候...")
    raw = chat(SYSTEM, user_msg)
    data = json.loads(raw)

    sections = []
    for page in data.get("pages", []):
        points = "\n".join(f"  • {bp}" for bp in page.get("bullet_points", []))
        notes = page.get("speaker_notes", "")
        content = f"{points}\n\n【演讲备注】{notes}"
        sections.append({
            "heading": f"第 {page['page_num']} 页：{page['page_title']}",
            "content": content,
        })

    ts = int(time.time())
    filename = f"PPT大纲_{ts}.docx"
    path = create_doc(filename, data.get("title", topic), sections, subtitle=f"用途：{scene}")
    print(f"\n生成完毕！文件路径：{path}")


if __name__ == "__main__":
    run()
