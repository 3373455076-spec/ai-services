#!/usr/bin/env python3
"""AI 自动交付服务平台 — 命令行入口"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

SERVICES = [
    ("简历优化",           "services.s01_resume",        "Word (.docx)",  "¥9.9"),
    ("小红书爆款文案",     "services.s02_xiaohongshu",   "Word (.docx)",  "¥5.9"),
    ("Excel 数据处理",     "services.s03_excel_process", "Excel (.xlsx)", "¥12.9"),
    ("PPT 大纲生成",       "services.s04_ppt_outline",   "Word (.docx)",  "¥8.9"),
    ("英语作文/邮件润色",  "services.s05_english_polish", "Word (.docx)", "¥6.9"),
    ("工作总结撰写",       "services.s06_work_summary",  "Word (.docx)",  "¥5.9"),
    ("论文降重改写",       "services.s07_paper_rewrite", "Word (.docx)",  "¥1.5/千字"),
    ("题库解析答题",       "services.s08_quiz_solver",   "PDF (.pdf)",    "¥3.9/10题"),
    ("海报文案生成",       "services.s09_poster_copy",   "PNG + TXT",     "¥6.9"),
    ("日程规划",           "services.s10_schedule",      "Excel (.xlsx)", "¥3.9"),
]


def show_menu():
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║             AI 自动交付服务平台  (共 10 项服务)             ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    for i, (name, _, fmt, price) in enumerate(SERVICES, 1):
        line = f"║  {i:>2}. {name:<20s}  输出: {fmt:<14s}  定价: {price:<10s}║"
        print(line)
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║   0. 退出                                                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")


def main():
    from config import API_KEY
    if not API_KEY:
        print("\n[提示] 请在 config.py 中填写 API_KEY，或设置环境变量 ANTHROPIC_API_KEY\n")
        sys.exit(1)

    while True:
        show_menu()
        choice = input("\n请输入服务编号 (1-10, 0退出): ").strip()

        if choice == "0":
            print("\n感谢使用，再见！")
            break

        if not choice.isdigit() or int(choice) < 1 or int(choice) > 10:
            print("\n[错误] 请输入 0-10 的数字。")
            continue

        idx = int(choice) - 1
        name, module_path, _, _ = SERVICES[idx]

        print(f"\n>>> 正在启动服务: {name}")
        print("-" * 40)

        try:
            mod = __import__(module_path, fromlist=["run"])
            mod.run()
        except KeyboardInterrupt:
            print("\n\n[中断] 已取消当前服务。")
        except Exception as e:
            print(f"\n[错误] 服务执行失败: {e}")

        input("\n按回车键返回主菜单...")


if __name__ == "__main__":
    main()
