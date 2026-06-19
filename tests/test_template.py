"""
Тесты модели Template: создание, сериализация, элементы.
"""
import pytest
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.template import (
    Template, TemplateElement, default_template,
    load_templates, save_templates
)
from app.models.label_context import LabelContext


class TestTemplateElement:
    def test_get_text_from_variable(self):
        ctx = LabelContext(article="ART-001", product_name="Кабель")
        elem = TemplateElement(variable="article")
        assert elem.get_text(ctx.get_variable) == "ART-001"

    def test_get_text_from_static(self):
        ctx = LabelContext()
        elem = TemplateElement(variable="", static_text="Статический текст")
        assert elem.get_text(ctx.get_variable) == "Статический текст"

    def test_get_text_variable_empty_falls_back_to_static(self):
        ctx = LabelContext()  # article пуст
        elem = TemplateElement(variable="article", static_text="Fallback")
        # article пуст, offer_id тоже пуст → ctx.get_variable("article") = ""
        # get_text возвращает static_text как fallback
        result = elem.get_text(ctx.get_variable)
        assert result == "Fallback"

    def test_to_dict_from_dict_roundtrip(self):
        elem = TemplateElement(
            type="barcode",
            x_mm=3.0, y_mm=2.0, w_mm=52.0, h_mm=14.0,
            variable="barcode",
            font_size=8.0,
            bold=True,
            align="center",
        )
        d = elem.to_dict()
        elem2 = TemplateElement.from_dict(d)
        assert elem2.type == "barcode"
        assert elem2.x_mm == 3.0
        assert elem2.bold is True
        assert elem2.align == "center"
        assert elem2.variable == "barcode"

    def test_from_dict_ignores_unknown_keys(self):
        """from_dict должен игнорировать неизвестные поля."""
        d = {"type": "text", "x_mm": 1.0, "unknown_field": "value"}
        elem = TemplateElement.from_dict(d)
        assert elem.type == "text"
        assert elem.x_mm == 1.0


class TestTemplate:
    def test_default_template(self):
        t = default_template()
        assert t.width_mm == 58.0
        assert t.height_mm == 40.0
        assert t.default is True
        assert len(t.elements) > 0

    def test_to_dict_from_dict(self):
        t = default_template()
        d = t.to_dict()
        t2 = Template.from_dict(d)
        assert t2.name == t.name
        assert t2.width_mm == t.width_mm
        assert t2.height_mm == t.height_mm
        assert len(t2.elements) == len(t.elements)

    def test_copy(self):
        t = default_template()
        t2 = t.copy()
        assert t2.id != t.id
        assert "копия" in t2.name.lower()
        assert t2.default is False
        # Изменение копии не влияет на оригинал
        t2.name = "Изменённый"
        assert t.name != "Изменённый"

    def test_save_load_roundtrip(self):
        t = default_template()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name

        try:
            save_templates(path, [t])
            loaded = load_templates(path)
            assert len(loaded) == 1
            assert loaded[0].name == t.name
            assert len(loaded[0].elements) == len(t.elements)
        finally:
            os.unlink(path)

    def test_load_nonexistent_returns_default(self):
        loaded = load_templates("/nonexistent/path/templates.json")
        assert len(loaded) == 1
        assert loaded[0].default is True

    def test_load_corrupted_json_returns_default(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            f.write("{invalid json{{")
            path = f.name
        try:
            loaded = load_templates(path)
            assert len(loaded) >= 1
        finally:
            os.unlink(path)
