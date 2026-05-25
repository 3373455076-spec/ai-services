"""AI 自动交付服务 — Web API (FastAPI)

启动方式:
    py api.py
    或 uvicorn api:app --host 0.0.0.0 --port 8000

每个服务为一个 POST 接口，接收 JSON 输入，返回生成的文件。
"""

import json
import time
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ai_client import chat
from formatters.word import create_doc, create_resume_doc, create_comparison_doc
from formatters.excel import create_schedule_excel, create_data_excel
from formatters.pdf import create_quiz_pdf
from formatters.image import create_poster
from config import OUTPUT_DIR

app = FastAPI(
    title="AI 自动交付服务平台",
    description="10 项 AI 服务，输入需求，返回成品文件",
    version="1.0.0",
)


def _ts():
    return int(time.time())


# ──────────────────────────────────────────
# 1. 简历优化
# ──────────────────────────────────────────
class ResumeInput(BaseModel):
    resume_text: str = Field(..., description="简历原文")
    target_job: str = Field(..., description="目标岗位名称")

@app.post("/api/resume", summary="1. 简历优化", tags=["求职办公"])
def resume(req: ResumeInput):
    system = (
        "你是一位专业简历优化师。根据用户提供的简历内容和目标岗位，优化简历。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：name, phone, email, target, summary(个人简介50-100字), "
        "sections(数组，每项含heading和items数组，items为字符串列表，"
        "建议包含：教育背景、工作经历、项目经验、专业技能等板块), "
        "suggestions(3条优化建议的数组)"
    )
    raw = chat(system, f"简历内容：\n{req.resume_text}\n\n目标岗位：{req.target_job}")
    data = json.loads(raw)
    path = create_resume_doc(f"resume_{_ts()}.docx", data)
    return FileResponse(path, filename="简历优化.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 2. 小红书文案
# ──────────────────────────────────────────
class XhsInput(BaseModel):
    keywords: str = Field(..., description="产品/话题关键词")
    style: str = Field("种草", description="风格：种草/测评/攻略/日常分享")

@app.post("/api/xiaohongshu", summary="2. 小红书爆款文案", tags=["文案创作"])
def xiaohongshu(req: XhsInput):
    system = (
        "你是小红书爆款文案写手。根据关键词和风格生成小红书文案。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：title(吸睛标题), content(正文300-500字，用emoji点缀), "
        "hashtags(5-8个话题标签数组), comments(3条评论区引导话术数组)"
    )
    raw = chat(system, f"关键词：{req.keywords}\n风格：{req.style}")
    data = json.loads(raw)
    sections = [
        {"heading": "标题", "content": data.get("title", "")},
        {"heading": "正文", "content": data.get("content", "")},
        {"heading": "话题标签", "content": "  ".join(
            f"#{t}" if not t.startswith("#") else t for t in data.get("hashtags", [])
        ), "style": "blue"},
        {"heading": "评论区引导", "content": "\n".join(
            f"{i}. {c}" for i, c in enumerate(data.get("comments", []), 1)
        ), "style": "quote"},
    ]
    path = create_doc(f"xhs_{_ts()}.docx", data.get("title", "小红书文案"), sections)
    return FileResponse(path, filename="小红书文案.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 3. Excel 数据处理
# ──────────────────────────────────────────
class ExcelInput(BaseModel):
    headers: list[str] = Field(..., description="表头列名")
    rows: list[list] = Field(..., description="数据行（二维数组）")
    instruction: str = Field(..., description="处理需求（一句话）")

@app.post("/api/excel", summary="3. Excel 数据处理", tags=["数据处理"])
def excel_process(req: ExcelInput):
    system = (
        "你是数据分析专家。用户提供了Excel数据的表头和样本数据，以及处理需求。"
        "请以纯JSON格式返回处理后的数据，不要包含markdown代码块，"
        "键为：result_headers(结果列名数组), result_rows(二维数组), "
        "chart_title(图表标题), summary(处理说明)"
    )
    user_msg = (
        f"表头：{json.dumps(req.headers, ensure_ascii=False)}\n"
        f"数据（共{len(req.rows)}行）：\n"
        f"{json.dumps(req.rows, ensure_ascii=False)}\n\n"
        f"处理需求：{req.instruction}"
    )
    raw = chat(system, user_msg)
    data = json.loads(raw)
    path = create_data_excel(
        f"data_{_ts()}.xlsx", req.headers, req.rows,
        data.get("result_headers", []), data.get("result_rows", []),
        chart_title=data.get("chart_title", ""),
    )
    return FileResponse(path, filename="数据处理结果.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ──────────────────────────────────────────
# 4. PPT 大纲
# ──────────────────────────────────────────
class PPTInput(BaseModel):
    topic: str = Field(..., description="演示主题")
    scene: str = Field("课堂汇报", description="用途：课堂汇报/工作述职/产品介绍")
    page_count: int = Field(15, description="期望页数 10-20")

@app.post("/api/ppt", summary="4. PPT 大纲生成", tags=["求职办公"])
def ppt_outline(req: PPTInput):
    system = (
        "你是PPT内容策划专家。根据主题、用途和页数生成完整的PPT逐页内容文稿。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：title(演示标题), pages(数组，每项含page_num, page_title, "
        "bullet_points(要点数组), speaker_notes(演讲备注))"
    )
    raw = chat(system, f"主题：{req.topic}\n用途场景：{req.scene}\n期望页数：{req.page_count}")
    data = json.loads(raw)
    sections = []
    for p in data.get("pages", []):
        points = "\n".join(f"  • {bp}" for bp in p.get("bullet_points", []))
        notes = p.get("speaker_notes", "")
        sections.append({
            "heading": f"第 {p['page_num']} 页：{p['page_title']}",
            "content": f"{points}\n\n【演讲备注】{notes}",
        })
    path = create_doc(f"ppt_{_ts()}.docx", data.get("title", req.topic), sections,
                       subtitle=f"用途：{req.scene}")
    return FileResponse(path, filename="PPT大纲.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 5. 英语润色
# ──────────────────────────────────────────
class EnglishInput(BaseModel):
    text: str = Field(..., description="英文原稿")
    scene: str = Field("雅思", description="场景：四六级/雅思/商务邮件/学术论文")
    level: str = Field("高水平", description="期望水平：B2/C1/native-like")

@app.post("/api/english", summary="5. 英语润色", tags=["外语优化"])
def english_polish(req: EnglishInput):
    system = (
        "你是英语写作专家。润色用户的英文文稿。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：polished_text(润色后完整文本), "
        "comparisons(数组，每项含original, revised, reason), "
        "overall_score(评分如85/100), tips(3条提升建议数组)"
    )
    raw = chat(system, f"目标场景：{req.scene}\n期望水平：{req.level}\n\n请润色以下英文文稿：\n{req.text}")
    data = json.loads(raw)
    comps = data.get("comparisons", [])
    path = create_comparison_doc(
        f"eng_{_ts()}.docx", "英语润色报告",
        [c.get("original", "") for c in comps],
        [c.get("revised", "") for c in comps],
        [c.get("reason", "") for c in comps],
        overall_score=data.get("overall_score", ""),
        tips=data.get("tips", []),
    )
    return FileResponse(path, filename="英语润色.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 6. 工作总结
# ──────────────────────────────────────────
class SummaryInput(BaseModel):
    work_points: str = Field(..., description="工作要点（关键词或流水账）")
    job_title: str = Field(..., description="岗位名称")
    audience: str = Field("直属领导", description="汇报对象：直属领导/部门总监/CEO")

@app.post("/api/summary", summary="6. 工作总结撰写", tags=["求职办公"])
def work_summary(req: SummaryInput):
    system = (
        "你是职场写作专家。根据用户的工作要点撰写结构化工作总结。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：title(总结标题), period(时间周期), "
        "sections(数组，每项含heading和content，必须包含："
        "本期成果、数据亮点、问题与改进、下期计划四个板块)"
    )
    raw = chat(system, f"岗位：{req.job_title}\n汇报对象：{req.audience}\n\n工作要点：\n{req.work_points}")
    data = json.loads(raw)
    sections = [{"heading": s["heading"], "content": s["content"]} for s in data.get("sections", [])]
    path = create_doc(f"summary_{_ts()}.docx", data.get("title", "工作总结"), sections,
                       subtitle=data.get("period", ""))
    return FileResponse(path, filename="工作总结.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 7. 论文降重
# ──────────────────────────────────────────
class PaperInput(BaseModel):
    paper_text: str = Field(..., description="需要降重的论文文本")

@app.post("/api/paper", summary="7. 论文降重改写", tags=["学业学习"])
def paper_rewrite(req: PaperInput):
    system = (
        "你是学术论文降重专家。对用户提供的论文文本进行降重改写，保持原意不变，"
        "调整句式结构与用词，显著降低重复率。请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：rewritten_paragraphs(数组，每项含original和rewritten两个字段，按段落逐段改写)"
    )
    raw = chat(system, req.paper_text)
    data = json.loads(raw)
    paragraphs = data.get("rewritten_paragraphs", [])
    sections = []
    for i, item in enumerate(paragraphs, 1):
        sections.append({"heading": f"段落 {i}", "content": item.get("rewritten", ""), "style": "blue"})
        sections.append({"content": f"【原文】{item.get('original', '')}", "style": "quote"})
    path = create_doc(f"paper_{_ts()}.docx", "论文降重改写报告", sections,
                       subtitle=f"共改写 {len(paragraphs)} 个段落")
    return FileResponse(path, filename="论文降重.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 8. 题库解析
# ──────────────────────────────────────────
class QuizInput(BaseModel):
    questions_text: str = Field(..., description="题目内容")
    subject: str = Field(..., description="学科（数学/物理/英语...）")
    exam_type: str = Field("", description="考试类型（高考/考研/期末...）")

@app.post("/api/quiz", summary="8. 题库解析答题", tags=["学业学习"])
def quiz_solver(req: QuizInput):
    system = (
        "你是教育辅导专家。解答用户提供的题目，给出详细解析。请以纯JSON格式返回，"
        "不要包含markdown代码块，键为：questions(数组，每项含number, question, answer, "
        "analysis(分步解题过程), knowledge(知识点归纳与易错提醒))"
    )
    raw = chat(system, f"学科：{req.subject}\n考试类型：{req.exam_type}\n\n题目内容：\n{req.questions_text}")
    data = json.loads(raw)
    questions = data.get("questions", [])
    title = " · ".join(filter(None, [req.subject, req.exam_type, "题库解析"]))
    path = create_quiz_pdf(f"quiz_{_ts()}.pdf", title, questions)
    return FileResponse(path, filename="题库解析.pdf", media_type="application/pdf")


# ──────────────────────────────────────────
# 9. 海报文案
# ──────────────────────────────────────────
class PosterInput(BaseModel):
    event_name: str = Field(..., description="活动名称")
    time_location: str = Field(..., description="时间和地点")
    audience: str = Field(..., description="目标受众")
    selling_point: str = Field(..., description="核心卖点")
    style: str = Field("活泼", description="风格：正式/活泼/文艺")

@app.post("/api/poster", summary="9. 海报文案生成", tags=["文案创作"])
def poster_copy(req: PosterInput):
    system = (
        "你是活动策划与文案专家。根据活动信息生成海报文案和推广文案。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：main_title(海报主标题，6字以内), subtitle(副标题), "
        "poster_body(海报正文150字以内), long_copy(推文版文案300-500字), "
        "moments_copies(3条朋友圈转发短文案数组), event_info(活动时间地点信息，用换行分隔)"
    )
    user_msg = (
        f"活动名称：{req.event_name}\n时间和地点：{req.time_location}\n"
        f"目标受众：{req.audience}\n核心卖点：{req.selling_point}\n风格：{req.style}"
    )
    raw = chat(system, user_msg)
    data = json.loads(raw)
    ts = _ts()
    png_path = create_poster(
        f"poster_{ts}.png", data["main_title"], data["subtitle"],
        data["poster_body"], event_info=data.get("event_info", ""),
    )
    # 同时返回文案文本作为 JSON header
    from starlette.responses import Response
    with open(png_path, "rb") as f:
        img_bytes = f.read()
    resp = Response(content=img_bytes, media_type="image/png")
    resp.headers["X-Long-Copy"] = data.get("long_copy", "")[:500]
    resp.headers["X-Moments-1"] = data.get("moments_copies", [""])[0][:200]
    resp.headers["Content-Disposition"] = "attachment; filename=poster.png"
    return resp


# ──────────────────────────────────────────
# 10. 日程规划
# ──────────────────────────────────────────
class ScheduleInput(BaseModel):
    todo_items: str = Field(..., description="待办事项（逗号分隔）")
    time_slots: str = Field(..., description="可用时间段（如 09:00-12:00, 14:00-18:00）")
    priorities: str = Field("", description="优先级偏好")

@app.post("/api/schedule", summary="10. 日程规划", tags=["数据处理"])
def schedule(req: ScheduleInput):
    system = (
        "你是时间管理专家。根据用户的待办事项、可用时间和优先级偏好，生成合理的日程安排。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：schedule(数组，每项含time_slot, task, duration, priority, notes), "
        "tips(2条效率提升建议数组)"
    )
    raw = chat(system, f"待办事项：{req.todo_items}\n可用时间段：{req.time_slots}\n优先级偏好：{req.priorities}")
    data = json.loads(raw)
    rows = [[s["time_slot"], s["task"], s["duration"], s["priority"], s["notes"]]
            for s in data.get("schedule", [])]
    path = create_schedule_excel(
        f"sched_{_ts()}.xlsx", "日程安排",
        ["时间段", "任务", "预估时长", "优先级", "备注"], rows,
        tips=data.get("tips", []),
    )
    return FileResponse(path, filename="日程规划.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ──────────────────────────────────────────
# 启动
# ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print("API 服务启动中...")
    print("接口文档：http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
