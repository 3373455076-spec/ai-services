import json
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_client import chat
from formatters.word import create_doc


SYSTEM_PROMPT = (
    "你是学术论文降重专家。对用户提供的论文文本进行降重改写，保持原意不变，"
    "调整句式结构与用词，显著降低重复率。请以纯JSON格式返回，不要包含markdown代码块，"
    "键为：rewritten_paragraphs（数组，每项含original和rewritten两个字段，按段落逐段改写）"
)


def run():
    print("\n论文降重改写")
    print("=" * 40)

    print("请粘贴需要降重改写的论文文本（输入空行结束）:")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    paper_text = "\n".join(lines)
    if not paper_text:
        print("未输入任何内容，已取消。")
        return

    print("\n正在调用AI进行降重改写，请稍候...")
    raw = chat(system=SYSTEM_PROMPT, user=paper_text)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("AI返回的内容不是有效JSON，无法解析。")
        print("原始返回：", raw[:500])
        return

    paragraphs = data.get("rewritten_paragraphs", [])
    if not paragraphs:
        print("AI未返回任何改写段落。")
        return

    # Build Word document sections
    sections = []
    for i, item in enumerate(paragraphs, 1):
        # Rewritten text in blue style
        sections.append({
            "heading": f"段落 {i}",
            "content": item.get("rewritten", ""),
            "style": "blue",
        })
        # Original text in quote style for reference
        sections.append({
            "content": f"【原文】{item.get('original', '')}",
            "style": "quote",
        })

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"论文降重_{timestamp}.docx"

    path = create_doc(
        filename=filename,
        title="论文降重改写报告",
        sections=sections,
        subtitle=f"共改写 {len(paragraphs)} 个段落",
    )

    print(f"\n已生成文件：{path}")
    print(f"共改写 {len(paragraphs)} 个段落。")


if __name__ == "__main__":
    run()
