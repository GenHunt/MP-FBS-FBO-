"""
Генератор внутренних этикеток 58×40 мм (и других размеров по шаблону).

Использует reportlab для PDF и python-barcode + Pillow для штрихкода Code128.
Координаты элементов задаются в мм.

Пример использования:
    from app.services.label_generator import LabelGenerator
    gen = LabelGenerator()
    pdf_bytes = gen.generate(template, label_context)
    gen.save(pdf_bytes, "output/label_123.pdf")
"""
from __future__ import annotations

import io
import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

MM = 2.8346456   # 1 mm в единицах reportlab (points, где 1 pt = 1/72 in)


def mm_to_pt(mm: float) -> float:
    return mm * MM


class LabelGenerator:
    """Генерирует PDF-этикетки по шаблону и контексту."""

    def __init__(self):
        self._check_deps()

    # ------------------------------------------------------------------
    # Зависимости
    # ------------------------------------------------------------------

    @staticmethod
    def _check_deps():
        missing = []
        try:
            import reportlab  # noqa: F401
        except ImportError:
            missing.append("reportlab")
        if missing:
            raise ImportError(
                f"Не установлены зависимости: {', '.join(missing)}. "
                "Запустите: pip install reportlab"
            )

    # ------------------------------------------------------------------
    # Генерация
    # ------------------------------------------------------------------

    def generate(self, template, ctx) -> bytes:
        """
        Генерировать PDF-этикетку.

        :param template: app.models.template.Template
        :param ctx:      app.models.label_context.LabelContext
        :return:         байты PDF
        """
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import portrait

        width_pt = mm_to_pt(template.width_mm)
        height_pt = mm_to_pt(template.height_mm)
        pagesize = (width_pt, height_pt)

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=pagesize)

        for elem in template.elements:
            if not elem.visible:
                continue
            try:
                if elem.type == "text":
                    self._draw_text(c, elem, ctx, height_pt)
                elif elem.type == "barcode":
                    self._draw_barcode(c, elem, ctx, height_pt)
            except Exception as e:
                logger.warning("Ошибка рисования элемента [%s]: %s", elem.type, e)

        c.save()
        return buf.getvalue()

    def _draw_text(self, c, elem, ctx, page_height_pt: float):
        """Нарисовать текстовый элемент."""
        from reportlab.lib import colors
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
        from reportlab.lib.units import mm

        text = elem.get_text(ctx.get_variable)
        if not text:
            if elem.required:
                text = f"[{elem.variable}]"
            else:
                return

        # Координаты: reportlab Y = снизу, наш шаблон — сверху
        x_pt = mm_to_pt(elem.x_mm)
        y_pt = page_height_pt - mm_to_pt(elem.y_mm) - mm_to_pt(elem.h_mm)
        w_pt = mm_to_pt(elem.w_mm)
        h_pt = mm_to_pt(elem.h_mm)

        align_map = {"left": TA_LEFT, "center": TA_CENTER, "right": TA_RIGHT}
        align = align_map.get(elem.align, TA_LEFT)

        font_name = _resolve_font(elem.font_family, elem.bold)
        font_size = elem.font_size

        style = ParagraphStyle(
            name="cell",
            fontName=font_name,
            fontSize=font_size,
            leading=font_size * 1.2,
            alignment=align,
            textColor=colors.black,
            wordWrap="LTR",
        )
        p = Paragraph(_escape_xml(text), style)
        w_avail, h_avail = p.wrap(w_pt, h_pt)
        # Вертикальная подгонка: если не влезает — уменьшаем шрифт
        if h_avail > h_pt and font_size > 5:
            for fs in range(int(font_size) - 1, 4, -1):
                style2 = ParagraphStyle(
                    name="cell_s",
                    fontName=font_name,
                    fontSize=fs,
                    leading=fs * 1.2,
                    alignment=align,
                    textColor=colors.black,
                    wordWrap="LTR",
                )
                p2 = Paragraph(_escape_xml(text), style2)
                _, h2 = p2.wrap(w_pt, h_pt)
                if h2 <= h_pt:
                    p = p2
                    break

        p.drawOn(c, x_pt, y_pt)

    def _draw_barcode(self, c, elem, ctx, page_height_pt: float):
        """Нарисовать штрихкод Code128."""
        value = elem.get_text(ctx.get_variable)
        if not value:
            value = elem.static_text or "0000000000"
        # Очищаем: только печатаемые ASCII
        value = "".join(ch for ch in value if 32 <= ord(ch) <= 126)
        if not value:
            value = "0000000000"

        x_pt = mm_to_pt(elem.x_mm)
        y_pt = page_height_pt - mm_to_pt(elem.y_mm) - mm_to_pt(elem.h_mm)
        w_pt = mm_to_pt(elem.w_mm)
        h_pt = mm_to_pt(elem.h_mm)

        bc_img = _render_barcode(value, w_pt, h_pt)
        if bc_img:
            c.drawImage(bc_img, x_pt, y_pt, width=w_pt, height=h_pt, mask="auto")
        else:
            # Fallback: нарисовать рамку с текстом
            from reportlab.lib import colors
            c.setStrokeColor(colors.black)
            c.rect(x_pt, y_pt, w_pt, h_pt)
            c.setFont("Helvetica", 6)
            c.drawCentredString(x_pt + w_pt / 2, y_pt + h_pt / 2 - 3, value)

    # ------------------------------------------------------------------
    # Сохранение
    # ------------------------------------------------------------------

    @staticmethod
    def save(pdf_bytes: bytes, path: str) -> None:
        """Сохранить байты PDF в файл."""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "wb") as f:
            f.write(pdf_bytes)

    def generate_preview_image(self, template, ctx) -> Optional[bytes]:
        """
        Генерировать PNG-превью первой страницы (для предпросмотра в редакторе).
        Требует pdf2image/poppler или Pillow. Fallback: схематичный PNG.
        """
        try:
            pdf_bytes = self.generate(template, ctx)
            return _pdf_to_png(pdf_bytes)
        except Exception as e:
            logger.warning("generate_preview_image: %s", e)
            return _schematic_preview_png(template, ctx)


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _resolve_font(family: str, bold: bool) -> str:
    """Резолвить имя шрифта для reportlab (встроенные Type1)."""
    base = "Helvetica"
    family_lower = family.lower()
    if "helvetica" in family_lower or "arial" in family_lower:
        base = "Helvetica"
    elif "times" in family_lower or "serif" in family_lower:
        base = "Times-Roman"
    elif "courier" in family_lower or "mono" in family_lower:
        base = "Courier"
    else:
        base = "Helvetica"
    if bold:
        if base == "Helvetica":
            return "Helvetica-Bold"
        if base == "Times-Roman":
            return "Times-Bold"
        if base == "Courier":
            return "Courier-Bold"
    return base


def _escape_xml(text: str) -> str:
    """Экранировать спецсимволы XML для reportlab Paragraph."""
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )


def _render_barcode(value: str, w_pt: float, h_pt: float):
    """
    Отрендерить штрихкод Code128 как изображение reportlab ImageReader.
    Приоритет: python-barcode → python-barcode без Pillow.
    """
    try:
        import barcode as pybarcode
        from barcode.writer import ImageWriter
        from reportlab.lib.utils import ImageReader
        import io

        bc_cls = pybarcode.get_barcode_class("code128")
        buf = io.BytesIO()
        bc = bc_cls(value, writer=ImageWriter())
        # Настраиваем writer чтобы минимизировать пустое пространство
        bc.write(
            buf,
            options={
                "module_width": 0.4,
                "module_height": h_pt / 2.8346,  # pt → mm (приближение)
                "quiet_zone": 2,
                "font_size": 5,
                "text_distance": 1,
                "write_text": True,
                "background": "white",
                "foreground": "black",
            },
        )
        buf.seek(0)
        return ImageReader(buf)
    except Exception as e:
        logger.debug("python-barcode/ImageWriter недоступен: %s", e)

    # Fallback: рисуем штрихкод вручную через Pillow (упрощённый EAN-13/Code128)
    try:
        from PIL import Image, ImageDraw, ImageFont
        from reportlab.lib.utils import ImageReader
        import io

        img_w = int(w_pt * 3)
        img_h = int(h_pt * 3)
        img = Image.new("RGB", (img_w, img_h), "white")
        draw = ImageDraw.Draw(img)

        # Упрощённая визуализация: рисуем полоски по символам
        bars = _code128_bars(value)
        bar_w = img_w / max(len(bars), 1)
        x = 0
        for i, bar in enumerate(bars):
            color = "black" if bar == 1 else "white"
            draw.rectangle([x, 2, x + bar_w, img_h - 14], fill=color)
            x += bar_w
        # Текст под штрихкодом
        draw.text((img_w // 2 - len(value) * 3, img_h - 13), value, fill="black")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return ImageReader(buf)
    except Exception as e:
        logger.debug("Pillow fallback недоступен: %s", e)
        return None


def _code128_bars(value: str) -> list:
    """Очень упрощённый генератор полосок Code128 B (только для визуализации)."""
    CODE128B_START = [2, 1, 1, 4, 1, 2]
    CODE128_STOP  = [2, 3, 3, 1, 1, 1, 2]
    CODE128B = {chr(i): i - 32 for i in range(32, 128)}

    bars = list(CODE128B_START)
    check = 104  # start code B
    for i, ch in enumerate(value):
        code = CODE128B.get(ch, 0)
        check += code * (i + 1)
        # упрощение: генерируем 3 полоски на символ (1/0/1)
        bars.extend([1, 0, 1])
    bars.extend([(check % 103) % 2, 1, 0])
    bars.extend(CODE128_STOP)
    return bars


def _pdf_to_png(pdf_bytes: bytes) -> Optional[bytes]:
    """Конвертировать первую страницу PDF в PNG через pdf2image."""
    try:
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_bytes, dpi=150, first_page=1, last_page=1)
        if images:
            buf = io.BytesIO()
            images[0].save(buf, format="PNG")
            return buf.getvalue()
    except Exception:
        pass
    return None


def _schematic_preview_png(template, ctx) -> bytes:
    """Схематичный PNG-превью без рендеринга PDF (fallback)."""
    try:
        from PIL import Image, ImageDraw
        SCALE = 4  # px/mm
        w = int(template.width_mm * SCALE)
        h = int(template.height_mm * SCALE)
        img = Image.new("RGB", (w, h), "white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w - 1, h - 1], outline="black")
        for elem in template.elements:
            if not elem.visible:
                continue
            x1 = int(elem.x_mm * SCALE)
            y1 = int(elem.y_mm * SCALE)
            x2 = int((elem.x_mm + elem.w_mm) * SCALE)
            y2 = int((elem.y_mm + elem.h_mm) * SCALE)
            color = "#AADDFF" if elem.type == "barcode" else "#DDFFAA"
            draw.rectangle([x1, y1, x2, y2], fill=color, outline="#555555")
            label = elem.variable or elem.static_text or elem.type
            draw.text((x1 + 2, y1 + 2), label[:20], fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        # Минимальный белый PNG 1x1
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
            b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
