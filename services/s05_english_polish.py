import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_client import chat
from formatters.word import create_comparison_doc


SYSTEM = (
    "你是英语写作专家。润色用户的英文文稿。"
    "请以纯JSON格式返回，不要包含markdown代码块，"
    "键为：polished_text(润色后完整文本), "
    "comparisons(数组，每项含original, revised, reason), "
    "overall_score(评分如85/100), tips(3条提升建议数组)"
)


def run():
    print("\n【英语作文 / 邮件润色】")
    print("=" * 40)

    print("请粘贴英文原稿（输入空行结束）:")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    text = "\n".join(lines)

    print("目标场景: 1.四六级  2.雅思  3.商务邮件  4.学术论文")
    scene_map = {"1": "四六级", "2": "雅思", "3": "商务邮件", "4": "学术论文"}
    sc = input("请选择 (1/2/3/4): ").strip()
    scene = scene_map.get(sc, sc)

    level = input("期望语言水平 (如 B2/C1/native-like，可留空): ").strip() or "高水平"

    user_msg = (
        f"目标场景：{scene}\n期望水平：{level}\n\n"
        f"请润色以下英文文稿：\n{text}"
    )

    print("\n正在润色，请稍候...")
    raw = chat(SYSTEM, user_msg)
    data = json.loads(raw)

    comps = data.get("comparisons", [])
    original_lines = [c.get("original", "") for c in comps]
    revised_lines = [c.get("revised", "") for c in comps]
    reasons = [c.get("reason", "") for c in comps]

    ts = int(time.time())
    filename = f"英语润色_{ts}.docx"
    path = create_comparison_doc(
        filename,
        title="英语润色报告",
        original_lines=original_lines,
        revised_lines=revised_lines,
        reasons=reasons,
        overall_score=data.get("overall_score", ""),
        tips=data.get("tips", []),
    )
    print(f"\n生成完毕！文件路径：{path}")


if __name__ == "__main__":
    run()
