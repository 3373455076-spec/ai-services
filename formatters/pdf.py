"""PDF generator with Chinese font support via fpdf2."""

from fpdf import FPDF
import os
from config import OUTPUT_DIR, get_chinese_font_path


class ChinesePDF(FPDF):
    def __init__(self):
        super().__init__()
        font_path = get_chinese_font_path()
        if font_path:
            self.add_font("zh", "", font_path, uni=True)
            self.add_font("zh", "B", font_path, uni=True)
        self._has_zh = bool(font_path)

    def _font(self, style="", size=11):
        if self._has_zh:
            self.set_font("zh", style, size)
        else:
            self.set_font("Helvetica", style, size)


def create_quiz_pdf(
    filename: str,
    title: str,
    questions: list[dict],
) -> str:
    """Create a quiz solution PDF.

    questions: list of dicts with keys:
      - number (str/int)
      - question (str)
      - answer (str)
      - analysis (str)
      - knowledge (str)
    """
    pdf = ChinesePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Title
    pdf._font("B", 18)
    pdf.cell(0, 15, title, ln=True, align="C")
    pdf.ln(8)

    for q in questions:
        # Question number and text
        pdf._font("B", 12)
        pdf.set_fill_color(240, 240, 250)
        pdf.multi_cell(
            0, 8,
            f"第 {q['number']} 题：{q.get('question', '')}",
            fill=True,
        )
        pdf.ln(2)

        # Answer
        pdf._font("B", 11)
        pdf.set_text_color(0, 112, 192)
        pdf.cell(0, 7, "【答案】", ln=True)
        pdf._font("", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 7, q.get("answer", ""))
        pdf.ln(2)

        # Analysis
        pdf._font("B", 11)
        pdf.set_text_color(0, 112, 192)
        pdf.cell(0, 7, "【解析】", ln=True)
        pdf._font("", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 7, q.get("analysis", ""))
        pdf.ln(2)

        # Knowledge point
        pdf._font("B", 11)
        pdf.set_text_color(0, 112, 192)
        pdf.cell(0, 7, "【知识点】", ln=True)
        pdf._font("", 11)
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(0, 7, q.get("knowledge", ""))
        pdf.ln(6)

        # Separator
        pdf.set_draw_color(200, 200, 200)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(6)

    path = os.path.join(OUTPUT_DIR, filename)
    pdf.output(path)
    return path
