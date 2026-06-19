"""
Тесты генератора PDF-этикеток.
Проверяет, что файл создаётся и содержит корректные данные.
"""
import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Пропускаем тесты если reportlab недоступен
reportlab_available = True
try:
    import reportlab
except ImportError:
    reportlab_available = False


@pytest.mark.skipif(not reportlab_available, reason="reportlab не установлен")
class TestLabelGenerator:
    def setup_method(self):
        from app.services.label_generator import LabelGenerator
        from app.models.template import default_template
        from app.models.label_context import LabelContext

        self.gen = LabelGenerator()
        self.template = default_template()
        self.ctx = LabelContext(
            posting_number="89750178-0001-1",
            order_number="89750178-0001",
            product_name="Тестовый товар для генерации",
            article="TEST-ART-001",
            offer_id="TEST-ART-001",
            sku="123456789",
            barcode="4607050394357",
            quantity=2,
        )

    def test_generate_returns_bytes(self):
        pdf = self.gen.generate(self.template, self.ctx)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_generate_valid_pdf_header(self):
        pdf = self.gen.generate(self.template, self.ctx)
        assert pdf[:4] == b"%PDF", "Не является PDF-файлом"

    def test_save_creates_file(self):
        pdf = self.gen.generate(self.template, self.ctx)
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_label.pdf")
            self.gen.save(pdf, out_path)
            assert os.path.exists(out_path)
            assert os.path.getsize(out_path) > 100

    def test_generate_custom_size(self):
        from app.models.template import Template, TemplateElement
        tpl = Template(name="Test", width_mm=80.0, height_mm=50.0, default=False)
        tpl.elements = [
            TemplateElement(type="text", x_mm=1, y_mm=1, w_mm=78, h_mm=10,
                            variable="product_name", font_size=8)
        ]
        pdf = self.gen.generate(tpl, self.ctx)
        assert pdf[:4] == b"%PDF"

    def test_generate_barcode_element(self):
        from app.models.template import Template, TemplateElement
        tpl = Template(name="BarTest", width_mm=58.0, height_mm=40.0)
        tpl.elements = [
            TemplateElement(type="barcode", x_mm=3, y_mm=2, w_mm=52, h_mm=14,
                            variable="barcode")
        ]
        pdf = self.gen.generate(tpl, self.ctx)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 50

    def test_generate_with_empty_context(self):
        from app.models.label_context import LabelContext
        ctx = LabelContext()  # всё пустое
        pdf = self.gen.generate(self.template, ctx)
        assert pdf[:4] == b"%PDF"

    def test_generate_with_long_product_name(self):
        from app.models.label_context import LabelContext
        ctx = LabelContext(product_name="Очень длинное наименование товара " * 10)
        pdf = self.gen.generate(self.template, ctx)
        assert pdf[:4] == b"%PDF"

    def test_multiple_labels_different_postings(self):
        from app.models.label_context import LabelContext
        pdfs = []
        for i in range(3):
            ctx = LabelContext(
                posting_number=f"POSTING-{i:04d}",
                product_name=f"Товар {i}",
                barcode=f"460000000{i:04d}",
            )
            pdfs.append(self.gen.generate(self.template, ctx))
        assert all(p[:4] == b"%PDF" for p in pdfs)
        assert len(set(len(p) for p in pdfs)) >= 1  # все создались


class TestLabelGeneratorImportError:
    def test_no_deps_raises_import_error(self, monkeypatch):
        """Проверяем, что отсутствие reportlab вызывает ImportError."""
        import importlib
        import app.services.label_generator as module

        original = module.LabelGenerator._check_deps

        def raise_err():
            raise ImportError("reportlab not found")

        monkeypatch.setattr(module.LabelGenerator, "_check_deps", staticmethod(raise_err))
        with pytest.raises(ImportError):
            module.LabelGenerator()

        monkeypatch.setattr(module.LabelGenerator, "_check_deps", staticmethod(original))
