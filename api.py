"""AI 自动交付服务 — Web API (FastAPI)

启动方式:
    py api.py
    或 uvicorn api:app --host 0.0.0.0 --port 8000
"""

import json
import time
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from starlette.responses import Response

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


@app.exception_handler(Exception)
async def global_error_handler(request, exc):
    tb = traceback.format_exc()
    print(f"[ERROR] {exc}\n{tb}")
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/", summary="健康检查")
def health():
    return {"status": "ok", "services": 10}


@app.get("/api/{service_name}", summary="查看接口说明")
def get_service_info(service_name: str):
    return {"service": service_name, "method": "POST"}


def _ts():
    return int(time.time())


async def _parse(request: Request) -> dict:
    """Parse request body from JSON, form data, or query params."""
    ct = request.headers.get("content-type", "")
    if "json" in ct:
        return await request.json()
    if "form" in ct or "urlencoded" in ct:
        form = await request.form()
        return dict(form)
    try:
        return await request.json()
    except Exception:
        form = await request.form()
        return dict(form)


def _get(data: dict, *keys, default=""):
    """Get value from dict by trying multiple possible keys."""
    for k in keys:
        if k in data:
            return data[k]
    return default


# ──────────────────────────────────────────
# 1. 简历优化
# ──────────────────────────────────────────
@app.post("/api/resume", summary="1. 简历优化", tags=["求职办公"])
async def resume(request: Request):
    data = await _parse(request)
    resume_text = _get(data, "简历原文", "resume_text")
    target_job = _get(data, "求职岗位", "target_job")
    system = (
        "你是一位专业简历优化师。根据用户提供的简历内容和目标岗位，优化简历。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：name, phone, email, target, summary(个人简介50-100字), "
        "sections(数组，每项含heading和items数组，items为字符串列表，"
        "建议包含：教育背景、工作经历、项目经验、专业技能等板块), "
        "suggestions(3条优化建议的数组)"
    )
    raw = chat(system, f"简历内容：\n{resume_text}\n\n目标岗位：{target_job}")
    result = json.loads(raw)
    path = create_resume_doc(f"resume_{_ts()}.docx", result)
    return FileResponse(path, filename="简历优化.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 2. 小红书文案
# ──────────────────────────────────────────
@app.post("/api/xiaohongshu", summary="2. 小红书爆款文案", tags=["文案创作"])
async def xiaohongshu(request: Request):
    data = await _parse(request)
    keywords = _get(data, "关键词", "keywords")
    style = _get(data, "风格", "style", default="种草")
    system = (
        "你是小红书爆款文案写手。根据关键词和风格生成小红书文案。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：title(吸睛标题), content(正文300-500字，用emoji点缀), "
        "hashtags(5-8个话题标签数组), comments(3条评论区引导话术数组)"
    )
    raw = chat(system, f"关键词：{keywords}\n风格：{style}")
    result = json.loads(raw)
    sections = [
        {"heading": "标题", "content": result.get("title", "")},
        {"heading": "正文", "content": result.get("content", "")},
        {"heading": "话题标签", "content": "  ".join(
            f"#{t}" if not t.startswith("#") else t for t in result.get("hashtags", [])
        ), "style": "blue"},
        {"heading": "评论区引导", "content": "\n".join(
            f"{i}. {c}" for i, c in enumerate(result.get("comments", []), 1)
        ), "style": "quote"},
    ]
    path = create_doc(f"xhs_{_ts()}.docx", result.get("title", "小红书文案"), sections)
    return FileResponse(path, filename="小红书文案.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 3. Excel 数据处理
# ──────────────────────────────────────────
@app.post("/api/excel", summary="3. Excel 数据处理", tags=["数据处理"])
async def excel_process(request: Request):
    data = await _parse(request)
    headers_raw = _get(data, "表头", "headers")
    rows_raw = _get(data, "数据行", "rows")
    instruction = _get(data, "处理需求", "instruction")
    if isinstance(headers_raw, str) and headers_raw.strip():
        try:
            headers = json.loads(headers_raw)
        except json.JSONDecodeError:
            headers = [h.strip() for h in headers_raw.split(",")]
    elif isinstance(headers_raw, list):
        headers = headers_raw
    else:
        headers = ["列1", "列2", "列3"]
    if isinstance(rows_raw, str) and rows_raw.strip():
        try:
            rows = json.loads(rows_raw)
        except json.JSONDecodeError:
            rows = [[c.strip() for c in r.split(",")] for r in rows_raw.strip().split("\n") if r.strip()]
    elif isinstance(rows_raw, list):
        rows = rows_raw
    else:
        rows = []
    system = (
        "你是数据分析专家。用户提供了Excel数据的表头和样本数据，以及处理需求。"
        "请以纯JSON格式返回处理后的数据，不要包含markdown代码块，"
        "键为：result_headers(结果列名数组), result_rows(二维数组), "
        "chart_title(图表标题), summary(处理说明)"
    )
    user_msg = (
        f"表头：{json.dumps(headers, ensure_ascii=False)}\n"
        f"数据（共{len(rows)}行）：\n"
        f"{json.dumps(rows, ensure_ascii=False)}\n\n"
        f"处理需求：{instruction}"
    )
    raw = chat(system, user_msg)
    result = json.loads(raw)
    path = create_data_excel(
        f"data_{_ts()}.xlsx", headers, rows,
        result.get("result_headers", []), result.get("result_rows", []),
        chart_title=result.get("chart_title", ""),
    )
    return FileResponse(path, filename="数据处理结果.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ──────────────────────────────────────────
# 4. PPT 大纲
# ──────────────────────────────────────────
@app.post("/api/ppt", summary="4. PPT 大纲生成", tags=["求职办公"])
async def ppt_outline(request: Request):
    data = await _parse(request)
    topic = _get(data, "主题", "topic")
    scene = _get(data, "用途", "scene", default="课堂汇报")
    page_count = _get(data, "页数", "page_count", default="10")
    system = (
        "你是PPT策划专家。根据主题生成PPT逐页内容。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：title(标题), pages(数组，每项含page_num, page_title, "
        "bullet_points(3个要点), speaker_notes(一句备注))"
    )
    raw = chat(system, f"主题：{topic}\n用途：{scene}\n页数：{page_count}", max_tokens=2048)
    result = json.loads(raw)
    sections = []
    for p in result.get("pages", []):
        points = "\n".join(f"  • {bp}" for bp in p.get("bullet_points", []))
        notes = p.get("speaker_notes", "")
        sections.append({
            "heading": f"第 {p['page_num']} 页：{p['page_title']}",
            "content": f"{points}\n\n【演讲备注】{notes}",
        })
    path = create_doc(f"ppt_{_ts()}.docx", result.get("title", topic), sections,
                       subtitle=f"用途：{scene}")
    return FileResponse(path, filename="PPT大纲.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 5. 英语润色
# ──────────────────────────────────────────
@app.post("/api/english", summary="5. 英语润色", tags=["外语优化"])
async def english_polish(request: Request):
    data = await _parse(request)
    text = _get(data, "英文原稿", "text")
    scene = _get(data, "场景", "scene", default="雅思")
    level = _get(data, "期望水平", "level", default="高水平")
    system = (
        "你是英语写作专家。润色用户的英文文稿。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：polished_text(润色后完整文本), "
        "comparisons(数组，每项含original, revised, reason), "
        "overall_score(评分如85/100), tips(3条提升建议数组)"
    )
    raw = chat(system, f"目标场景：{scene}\n期望水平：{level}\n\n请润色以下英文文稿：\n{text}")
    result = json.loads(raw)
    comps = result.get("comparisons", [])
    path = create_comparison_doc(
        f"eng_{_ts()}.docx", "英语润色报告",
        [c.get("original", "") for c in comps],
        [c.get("revised", "") for c in comps],
        [c.get("reason", "") for c in comps],
        overall_score=result.get("overall_score", ""),
        tips=result.get("tips", []),
    )
    return FileResponse(path, filename="英语润色.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 6. 工作总结
# ──────────────────────────────────────────
@app.post("/api/summary", summary="6. 工作总结撰写", tags=["求职办公"])
async def work_summary(request: Request):
    data = await _parse(request)
    work_points = _get(data, "工作要点", "work_points")
    job_title = _get(data, "岗位名称", "job_title")
    audience = _get(data, "汇报对象", "audience", default="直属领导")
    system = (
        "你是职场写作专家。根据用户的工作要点撰写结构化工作总结。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：title(总结标题), period(时间周期), "
        "sections(数组，每项含heading和content，必须包含："
        "本期成果、数据亮点、问题与改进、下期计划四个板块)"
    )
    raw = chat(system, f"岗位：{job_title}\n汇报对象：{audience}\n\n工作要点：\n{work_points}")
    result = json.loads(raw)
    sections = [{"heading": s["heading"], "content": s["content"]} for s in result.get("sections", [])]
    path = create_doc(f"summary_{_ts()}.docx", result.get("title", "工作总结"), sections,
                       subtitle=result.get("period", ""))
    return FileResponse(path, filename="工作总结.docx",
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ──────────────────────────────────────────
# 7. 论文降重
# ──────────────────────────────────────────
@app.post("/api/paper", summary="7. 论文降重改写", tags=["学业学习"])
async def paper_rewrite(request: Request):
    data = await _parse(request)
    paper_text = _get(data, "论文文本", "paper_text")
    system = (
        "你是学术论文降重专家。对用户提供的论文文本进行降重改写，保持原意不变，"
        "调整句式结构与用词，显著降低重复率。请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：rewritten_paragraphs(数组，每项含original和rewritten两个字段，按段落逐段改写)"
    )
    raw = chat(system, paper_text)
    result = json.loads(raw)
    paragraphs = result.get("rewritten_paragraphs", [])
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
@app.post("/api/quiz", summary="8. 题库解析答题", tags=["学业学习"])
async def quiz_solver(request: Request):
    data = await _parse(request)
    questions_text = _get(data, "题目内容", "questions_text")
    subject = _get(data, "学科", "subject")
    exam_type = _get(data, "考试类型", "exam_type", default="")
    system = (
        "你是教育辅导专家。解答用户提供的题目，给出详细解析。请以纯JSON格式返回，"
        "不要包含markdown代码块，键为：questions(数组，每项含number, question, answer, "
        "analysis(分步解题过程), knowledge(知识点归纳与易错提醒))"
    )
    raw = chat(system, f"学科：{subject}\n考试类型：{exam_type}\n\n题目内容：\n{questions_text}")
    result = json.loads(raw)
    questions = result.get("questions", [])
    title = " · ".join(filter(None, [subject, exam_type, "题库解析"]))
    path = create_quiz_pdf(f"quiz_{_ts()}.pdf", title, questions)
    return FileResponse(path, filename="题库解析.pdf", media_type="application/pdf")


# ──────────────────────────────────────────
# 9. 海报文案
# ──────────────────────────────────────────
@app.post("/api/poster", summary="9. 海报文案生成", tags=["文案创作"])
async def poster_copy(request: Request):
    data = await _parse(request)
    event_name = _get(data, "活动名称", "event_name")
    time_location = _get(data, "时间地点", "time_location")
    audience = _get(data, "目标受众", "audience")
    selling_point = _get(data, "核心卖点", "selling_point")
    style = _get(data, "风格", "style", default="活泼")
    system = (
        "你是活动策划与文案专家。根据活动信息生成海报文案和推广文案。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：main_title(海报主标题，6字以内), subtitle(副标题), "
        "poster_body(海报正文150字以内), long_copy(推文版文案300-500字), "
        "moments_copies(3条朋友圈转发短文案数组), event_info(活动时间地点信息，用换行分隔)"
    )
    user_msg = (
        f"活动名称：{event_name}\n时间和地点：{time_location}\n"
        f"目标受众：{audience}\n核心卖点：{selling_point}\n风格：{style}"
    )
    raw = chat(system, user_msg)
    result = json.loads(raw)
    ts = _ts()
    png_path = create_poster(
        f"poster_{ts}.png", result["main_title"], result["subtitle"],
        result["poster_body"], event_info=result.get("event_info", ""),
    )
    with open(png_path, "rb") as f:
        img_bytes = f.read()
    resp = Response(content=img_bytes, media_type="image/png")
    resp.headers["Content-Disposition"] = "attachment; filename=poster.png"
    return resp


# ──────────────────────────────────────────
# 10. 日程规划
# ──────────────────────────────────────────
@app.post("/api/schedule", summary="10. 日程规划", tags=["数据处理"])
async def schedule(request: Request):
    data = await _parse(request)
    todo_items = _get(data, "待办事项", "todo_items")
    time_slots = _get(data, "可用时间", "time_slots")
    priorities = _get(data, "优先级偏好", "priorities", default="")
    system = (
        "你是时间管理专家。根据用户的待办事项、可用时间和优先级偏好，生成合理的日程安排。"
        "请以纯JSON格式返回，不要包含markdown代码块，"
        "键为：schedule(数组，每项含time_slot, task, duration, priority, notes), "
        "tips(2条效率提升建议数组)"
    )
    raw = chat(system, f"待办事项：{todo_items}\n可用时间段：{time_slots}\n优先级偏好：{priorities}")
    result = json.loads(raw)
    rows = [[s["time_slot"], s["task"], s["duration"], s["priority"], s["notes"]]
            for s in result.get("schedule", [])]
    path = create_schedule_excel(
        f"sched_{_ts()}.xlsx", "日程安排",
        ["时间段", "任务", "预估时长", "优先级", "备注"], rows,
        tips=result.get("tips", []),
    )
    return FileResponse(path, filename="日程规划.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ──────────────────────────────────────────
# 启动
# ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"API 服务启动中... 端口: {port}")
    print(f"接口文档：http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)
