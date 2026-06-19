"""
Label generator - creates label images from templates
"""
import logging
import io
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LabelGenerator:
    """Generates label images from templates"""

    MM_TO_PX = 11.811  # 300 DPI: 1mm = 11.811px

    def __init__(self, dpi: int = 203):
        self.dpi = dpi
        self.px_per_mm = dpi / 25.4  # pixels per mm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_label(self, template, data: Dict[str, Any]):
        """
        Generate a PIL Image for the given template and data dict.

        Args:
            template: Template instance.
            data:     Dictionary of variable values.

        Returns:
            PIL.Image.Image or None on failure.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            width_px = int(template.label_width * self.px_per_mm)
            height_px = int(template.label_height * self.px_per_mm)

            image = Image.new('RGB', (width_px, height_px), 'white')
            draw = ImageDraw.Draw(image)

            for element in template.elements:
                if not element.visible:
                    continue
                try:
                    self._draw_element(draw, image, element, data)
                except Exception as e:
                    logger.warning(f"Failed to draw element {element.element_id}: {e}")

            return image

        except ImportError:
            logger.error("PIL is not installed; cannot generate labels")
            return None
        except Exception as e:
            logger.error(f"Failed to generate label: {e}")
            return None

    def generate_label_pdf(self, template, data: Dict[str, Any]) -> Optional[bytes]:
        """
        Generate a single-page PDF containing the label.

        Returns:
            PDF bytes or None.
        """
        image = self.generate_label(template, data)
        if image is None:
            return None
        try:
            buf = io.BytesIO()
            image.save(buf, format='PDF', resolution=self.dpi)
            return buf.getvalue()
        except Exception as e:
            logger.error(f"Failed to convert label to PDF: {e}")
            return None

    # ------------------------------------------------------------------
    # Internal drawing helpers
    # ------------------------------------------------------------------

    def _mm_to_px(self, mm: float) -> int:
        return int(mm * self.px_per_mm)

    def _draw_element(self, draw, image, element, data: Dict[str, Any]) -> None:
        from src.models.template import ElementType

        x = self._mm_to_px(element.x)
        y = self._mm_to_px(element.y)
        w = self._mm_to_px(element.width)
        h = self._mm_to_px(element.height)

        value = data.get(element.variable, '') if element.variable else ''

        if element.element_type == ElementType.TEXT:
            self._draw_text(draw, x, y, w, h, str(value), element)

        elif element.element_type == ElementType.BARCODE:
            self._draw_barcode(image, x, y, w, h, str(value), element)

        elif element.element_type == ElementType.LINE:
            draw.line([(x, y), (x + w, y + h)], fill='black', width=2)

    def _draw_text(self, draw, x, y, w, h, text, element) -> None:
        from PIL import ImageFont

        try:
            font = ImageFont.truetype("arial.ttf", element.font_size * 2)
        except Exception:
            try:
                from PIL import ImageFont as _IF
                font = _IF.load_default()
            except Exception:
                font = None

        fill = 'black'
        if font:
            draw.text((x, y), text, fill=fill, font=font)
        else:
            draw.text((x, y), text, fill=fill)

    def _draw_barcode(self, image, x, y, w, h, value, element) -> None:
        if not value:
            return
        try:
            import barcode
            from barcode.writer import ImageWriter
            import io
            from PIL import Image

            barcode_class = barcode.get_barcode_class(
                element.barcode_type.lower().replace('128', 'code128')
                if '128' in element.barcode_type else element.barcode_type.lower()
            )
            buf = io.BytesIO()
            bc = barcode_class(value, writer=ImageWriter())
            bc.write(buf, options={'write_text': False})
            buf.seek(0)
            bc_image = Image.open(buf).convert('RGB')
            bc_image = bc_image.resize((w, h), Image.LANCZOS)
            image.paste(bc_image, (x, y))
        except Exception as e:
            logger.warning(f"Failed to render barcode '{value}': {e}")
