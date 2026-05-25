import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_client import chat
from formatters.word import create_doc


SYSTEM = (
    "你是职场写作专家。根据用户的工作要点撰写结构化工作总结。"
    "请以纯JSON格式返回，不要包含markdown代码块，"
    "键为：title(总结标题), period(时间周期), "
    "sections(数组，每项含heading和content，必须包含："
    "本期成果、数据亮点、问题与改进、下期计划四个板块)"
)


def run():
    print("\n【周报 / 月报 / 工作总结撰写】")
    print("=" * 40)

    print("请输入本期工作要点（关键词或流水账均可，输入空行结束）:")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    points = "\n".join(lines)

    job_title = input("你的岗位名称: ").strip()

    print("汇报对象: 1.直属领导  2.部门总监  3.CEO")
    aud_map = {"1": "直属领导", "2": "部门总监", "3": "CEO"}
    ac = input("请选择 (1/2/3): ").strip()
    audience = aud_map.get(ac, ac)

    user_msg = (
        f"岗位：{job_title}\n汇报对象：{audience}\n\n"
        f"工作要点：\n{points}\n\n请撰写结构化工作总结。"
    )

    print("\n正在撰写工作总结，请稍候...")
    raw = chat(SYSTEM, user_msg)
    data = json.loads(raw)

    sections = []
    for sec in data.get("sections", []):
        sections.append({
            "heading": sec.get("heading", ""),
            "content": sec.get("content", ""),
        })

    ts = int(time.time())
    filename = f"工作总结_{ts}.docx"
    path = create_doc(
        filename,
        data.get("title", "工作总结"),
        sections,
        subtitle=data.get("period", ""),
    )
    print(f"\n生成完毕！文件路径：{path}")


if __name__ == "__main__":
    run()
