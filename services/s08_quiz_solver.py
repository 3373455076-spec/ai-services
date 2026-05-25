import json
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_client import chat
from formatters.pdf import create_quiz_pdf


SYSTEM_PROMPT = (
    "你是教育辅导专家。解答用户提供的题目，给出详细解析。请以纯JSON格式返回，"
    "不要包含markdown代码块，键为：questions（数组，每项含number, question, answer, "
    "analysis（分步解题过程）, knowledge（知识点归纳与易错提醒））"
)


def run():
    print("\n题库解析与答题")
    print("=" * 40)

    print("请粘贴题目内容（输入空行结束）:")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    questions_text = "\n".join(lines)
    if not questions_text:
        print("未输入任何内容，已取消。")
        return

    subject = input("请输入学科（如 数学、物理、英语）：").strip()
    exam_type = input("请输入考试类型（如 高考、考研、期末考试）：").strip()

    user_message = f"学科：{subject}\n考试类型：{exam_type}\n\n题目内容：\n{questions_text}"

    print("\n正在调用AI进行解析，请稍候...")
    raw = chat(system=SYSTEM_PROMPT, user=user_message)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("AI返回的内容不是有效JSON，无法解析。")
        print("原始返回：", raw[:500])
        return

    questions = data.get("questions", [])
    if not questions:
        print("AI未返回任何题目解析。")
        return

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"题库解析_{timestamp}.pdf"

    title_parts = []
    if subject:
        title_parts.append(subject)
    if exam_type:
        title_parts.append(exam_type)
    title_parts.append("题库解析")
    title = " · ".join(title_parts)

    path = create_quiz_pdf(
        filename=filename,
        title=title,
        questions=questions,
    )

    print(f"\n已生成文件：{path}")
    print(f"共解析 {len(questions)} 道题目。")


if __name__ == "__main__":
    run()
