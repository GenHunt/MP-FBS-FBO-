"""
Тесты модели LabelContext: подстановка переменных, fallback, from_dict.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.label_context import LabelContext


class TestLabelContextVariables:
    def test_basic_variables(self):
        ctx = LabelContext(
            posting_number="89750178-0001-1",
            order_number="89750178-0001",
            product_name="Кабель USB-C 1м",
            article="CBL-USB-C-1M",
            offer_id="CBL-USB-C-1M",
            sku="555444333",
            barcode="4610196534213",
            manufacturer_part_number="UC1M-WH",
            quantity=3,
        )
        assert ctx.get_variable("posting_number") == "89750178-0001-1"
        assert ctx.get_variable("order_number") == "89750178-0001"
        assert ctx.get_variable("product_name") == "Кабель USB-C 1м"
        assert ctx.get_variable("article") == "CBL-USB-C-1M"
        assert ctx.get_variable("barcode") == "4610196534213"
        assert ctx.get_variable("sku") == "555444333"
        assert ctx.get_variable("quantity") == "3"
        assert ctx.get_variable("manufacturer_part_number") == "UC1M-WH"

    def test_article_fallback_to_offer_id(self):
        """Если article пуст — должен вернуть offer_id."""
        ctx = LabelContext(article="", offer_id="OFFER-123")
        assert ctx.get_variable("article") == "OFFER-123"
        assert ctx.article == "OFFER-123"  # __post_init__ должен был заполнить

    def test_article_no_fallback_when_set(self):
        """Если article задан явно — offer_id не используется."""
        ctx = LabelContext(article="REAL-ART", offer_id="OFFER-456")
        assert ctx.get_variable("article") == "REAL-ART"

    def test_unknown_variable_returns_empty(self):
        ctx = LabelContext()
        assert ctx.get_variable("nonexistent") == ""

    def test_date_time_auto_fill(self):
        """date и time заполняются автоматически если не заданы."""
        ctx = LabelContext()
        assert len(ctx.date) == 10   # DD.MM.YYYY
        assert len(ctx.time) == 5    # HH:MM

    def test_date_time_explicit(self):
        ctx = LabelContext(date="01.01.2025", time="12:00")
        assert ctx.get_variable("date") == "01.01.2025"
        assert ctx.get_variable("time") == "12:00"

    def test_from_dict(self):
        d = {
            "posting_number": "POSTING-001",
            "product_name": "Товар тестовый",
            "article": "ART-XYZ",
            "offer_id": "OFFER-XYZ",
            "sku": "1234",
            "barcode": "1234567890128",
            "quantity": 5,
        }
        ctx = LabelContext.from_dict(d)
        assert ctx.posting_number == "POSTING-001"
        assert ctx.product_name == "Товар тестовый"
        assert ctx.quantity == 5
        assert ctx.barcode == "1234567890128"

    def test_from_dict_missing_fields(self):
        """from_dict должен работать при отсутствии полей."""
        ctx = LabelContext.from_dict({})
        assert ctx.posting_number == ""
        assert ctx.quantity == 1

    def test_to_dict_roundtrip(self):
        ctx = LabelContext(
            posting_number="P-001",
            product_name="Test",
            article="ART",
            quantity=2,
        )
        d = ctx.to_dict()
        ctx2 = LabelContext.from_dict(d)
        assert ctx2.posting_number == ctx.posting_number
        assert ctx2.product_name == ctx.product_name
        assert ctx2.article == ctx.article
        assert ctx2.quantity == ctx.quantity

    def test_quantity_type(self):
        ctx = LabelContext.from_dict({"quantity": "7"})
        assert ctx.quantity == 7
        assert isinstance(ctx.quantity, int)


class TestLabelContextEdgeCases:
    def test_special_chars_in_barcode(self):
        ctx = LabelContext(barcode="123-456 ABC")
        assert ctx.get_variable("barcode") == "123-456 ABC"

    def test_long_product_name(self):
        long_name = "А" * 500
        ctx = LabelContext(product_name=long_name)
        assert len(ctx.get_variable("product_name")) == 500

    def test_unicode_product_name(self):
        ctx = LabelContext(product_name="Держатель für телефон 📱")
        assert "Держатель" in ctx.get_variable("product_name")
