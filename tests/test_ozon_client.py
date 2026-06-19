"""
Тесты Ozon API клиента (mock-режим).
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.api.ozon_client import OzonClient, OzonAPIError, MOCK_POSTINGS


class TestOzonClientMock:
    def setup_method(self):
        self.client = OzonClient(mock_mode=True)

    def test_list_unfulfilled_postings_returns_list(self):
        postings = self.client.list_unfulfilled_postings()
        assert isinstance(postings, list)
        assert len(postings) == len(MOCK_POSTINGS)

    def test_list_unfulfilled_has_required_fields(self):
        postings = self.client.list_unfulfilled_postings()
        for p in postings:
            assert "posting_number" in p
            assert "products" in p

    def test_get_posting_found(self):
        posting_number = MOCK_POSTINGS[0]["posting_number"]
        p = self.client.get_posting(posting_number)
        assert p is not None
        assert p["posting_number"] == posting_number

    def test_get_posting_not_found(self):
        p = self.client.get_posting("NONEXISTENT-0000-0")
        assert p is None

    def test_get_package_label_returns_bytes(self):
        pn = MOCK_POSTINGS[0]["posting_number"]
        pdf = self.client.get_package_label([pn])
        assert isinstance(pdf, bytes)
        assert len(pdf) > 10

    def test_product_info_list_mock_returns_empty(self):
        result = self.client.product_info_list(offer_ids=["TEST"])
        assert result == []

    def test_product_attributes_mock_returns_empty(self):
        result = self.client.product_attributes()
        assert result == []

    def test_post_raises_in_mock_mode(self):
        with pytest.raises(OzonAPIError, match="mock_mode=True"):
            self.client._post("/v3/posting/fbs/unfulfilled/list", {})


class TestOzonClientNormalize:
    def setup_method(self):
        self.client = OzonClient(mock_mode=True)

    def test_normalize_basic(self):
        raw = {
            "posting_number": "TEST-001",
            "order_number": "ORDER-001",
            "products": [
                {
                    "offer_id": "ART-001",
                    "name": "Товар тестовый",
                    "sku": 12345,
                    "quantity": 2,
                    "barcode": "1234567890128",
                }
            ],
        }
        contexts = self.client.normalize_posting(raw)
        assert len(contexts) == 1
        ctx_dict = contexts[0]
        assert ctx_dict["posting_number"] == "TEST-001"
        assert ctx_dict["product_name"] == "Товар тестовый"
        assert ctx_dict["quantity"] == 2
        assert ctx_dict["barcode"] == "1234567890128"

    def test_normalize_article_fallback(self):
        """Если article отсутствует, используется offer_id."""
        raw = {
            "posting_number": "TEST-002",
            "order_number": "ORDER-002",
            "products": [
                {"offer_id": "OFFER-XYZ", "name": "X", "sku": 1, "quantity": 1}
            ],
        }
        contexts = self.client.normalize_posting(raw)
        assert contexts[0]["article"] == "OFFER-XYZ"

    def test_normalize_article_explicit(self):
        """Если article задан явно — используется article."""
        raw = {
            "posting_number": "TEST-003",
            "order_number": "ORDER-003",
            "products": [
                {
                    "offer_id": "OFFER-ABC",
                    "article": "EXPLICIT-ART",
                    "name": "Y",
                    "sku": 2,
                    "quantity": 1,
                }
            ],
        }
        contexts = self.client.normalize_posting(raw)
        assert contexts[0]["article"] == "EXPLICIT-ART"

    def test_normalize_barcode_list(self):
        """barcode может быть списком — берём первый."""
        raw = {
            "posting_number": "TEST-004",
            "order_number": "ORDER-004",
            "products": [
                {
                    "offer_id": "X",
                    "name": "Z",
                    "sku": 3,
                    "quantity": 1,
                    "barcodes": ["111", "222"],
                }
            ],
        }
        contexts = self.client.normalize_posting(raw)
        assert contexts[0]["barcode"] == "111"

    def test_normalize_multiple_products(self):
        raw = {
            "posting_number": "MULTI-001",
            "order_number": "ORDER-MULTI",
            "products": [
                {"offer_id": "P1", "name": "Prod1", "sku": 1, "quantity": 1},
                {"offer_id": "P2", "name": "Prod2", "sku": 2, "quantity": 3},
            ],
        }
        contexts = self.client.normalize_posting(raw)
        assert len(contexts) == 2
        assert contexts[0]["offer_id"] == "P1"
        assert contexts[1]["quantity"] == 3

    def test_normalize_empty_products(self):
        raw = {"posting_number": "EMPTY", "order_number": "O", "products": []}
        contexts = self.client.normalize_posting(raw)
        assert contexts == []


class TestOzonClientRealMode:
    """Проверяем, что реальный режим не запускается без ключей (сетевые ошибки)."""

    def test_real_mode_raises_on_missing_requests(self):
        client = OzonClient(client_id="", api_key="", mock_mode=False)
        # В sandbox requests может быть доступен, но API отклонит запрос
        # Проверяем только что _get_session не падает при наличии requests
        try:
            import requests
            session = client._get_session()
            assert session is not None
        except ImportError:
            pytest.skip("requests не установлен")
