"""简历优化服务 - 输出Word (.docx)"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from ai_client import chat
from formatters.word import create_resume_doc

SYSTEM_PROMPT = (
    "你是一位专业简历优化师。根据用户提供的简历内容和目标岗位，优化简历。"
    "请以纯JSON格式返回，不要包含markdown代码块，"
    "键为：name, phone, email, target, summary(个人简介50-100字), "
    "sections(数组，每项含heading和items数组，items为字符串列表，"
    "建议包含：教育背景、工作经历、项目经验、专业技能等板块), "
    "suggestions(3条优化建议的数组)"
)


def run():
    print("\n简历优化服务")
    print("=" * 40)

    print("请粘贴您的简历内容（输入空行结束）：")
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    resume_text = "\n".join(lines)

    target_job = input("请输入目标岗位名称：").strip()

    user_msg = f"简历内容：\n{resume_text}\n\n目标岗位：{target_job}"

    print("\n正在优化简历，请稍候...")
    raw = chat(SYSTEM_PROMPT, user_msg)

    data = json.loads(raw)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"resume_优化_{timestamp}.docx"

    path = create_resume_doc(filename, data)
    print(f"\n简历已生成：{path}")


if __name__ == "__main__":
    run()
