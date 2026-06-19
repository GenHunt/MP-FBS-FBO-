"""
Клиент Ozon Seller API.
Документация: https://docs.ozon.ru/api/seller/

Каждый запрос содержит заголовки:
  Client-Id: <ваш Client-Id>
  Api-Key: <ваш API-Key>

Класс поддерживает mock-режим (без реальных ключей) и real-режим.
"""
from __future__ import annotations

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock-данные для тестирования без реального аккаунта Ozon
# ---------------------------------------------------------------------------
MOCK_POSTINGS = [
    {
        "posting_number": "89750178-0001-1",
        "order_number": "89750178-0001",
        "status": "awaiting_packaging",
        "products": [
            {
                "offer_id": "ART-001",
                "name": "Держатель для телефона автомобильный",
                "sku": 123456789,
                "quantity": 2,
                "article": "ART-001",
                "barcode": "4607050394357",
            }
        ],
    },
    {
        "posting_number": "89750178-0002-1",
        "order_number": "89750178-0002",
        "status": "awaiting_packaging",
        "products": [
            {
                "offer_id": "CASE-XL-BLK",
                "name": "Чехол для смартфона XL чёрный",
                "sku": 987654321,
                "quantity": 1,
                "article": "CASE-XL-BLK",
                "barcode": "4630037330178",
            }
        ],
    },
    {
        "posting_number": "89750178-0003-1",
        "order_number": "89750178-0003",
        "status": "awaiting_packaging",
        "products": [
            {
                "offer_id": "CBL-USB-C-1M",
                "name": "Кабель USB-C 1 метр нейлоновый белый",
                "sku": 555444333,
                "quantity": 3,
                "article": "CBL-USB-C-1M",
                "barcode": "4610196534213",
                "manufacturer_part_number": "UC1M-WH",
            }
        ],
    },
]


class OzonAPIError(Exception):
    """Ошибка при обращении к Ozon API."""

    def __init__(self, message: str, status_code: int = 0, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class OzonCredentialError(OzonAPIError):
    """Некорректные учётные данные (Client-Id / Api-Key)."""


# Понятное пользователю сообщение, без низкоуровневого 'latin-1 codec'.
CREDENTIAL_ERROR_MESSAGE = (
    "Client-Id и Api-Key должны быть скопированы из кабинета Ozon "
    "без русских букв, пробелов и переносов строк. "
    "Проверьте поля авторизации."
)


def _sanitize_credential(value: str) -> str:
    """Убрать пробелы/переносы строк по краям значения заголовка."""
    if value is None:
        return ""
    return str(value).strip()


def _validate_credentials(client_id: str, api_key: str) -> None:
    """
    Проверить, что Client-Id и Api-Key пригодны для HTTP-заголовков.

    requests кодирует значения заголовков в latin-1, поэтому кириллица и
    другие не-ASCII символы вызывают UnicodeEncodeError ещё до отправки
    запроса. Здесь мы перехватываем это заранее и показываем понятное
    сообщение вместо "'latin-1' codec can't encode...".
    """
    for value in (client_id, api_key):
        if not value:
            raise OzonCredentialError(CREDENTIAL_ERROR_MESSAGE)
        try:
            value.encode("ascii")
        except UnicodeEncodeError:
            raise OzonCredentialError(CREDENTIAL_ERROR_MESSAGE)


class OzonClient:
    """
    Клиент Ozon Seller API.

    Аргументы:
        client_id  — Client-Id из настроек кабинета Ozon.
        api_key    — Api-Key из настроек кабинета Ozon.
        mock_mode  — если True, возвращает тестовые данные без сетевых запросов.
    """

    BASE_URL = "https://api-seller.ozon.ru"

    def __init__(self, client_id: str = "", api_key: str = "", mock_mode: bool = True):
        self.client_id = _sanitize_credential(client_id)
        self.api_key = _sanitize_credential(api_key)
        self.mock_mode = mock_mode
        self._session = None

    # ------------------------------------------------------------------
    # Низкоуровневый HTTP
    # ------------------------------------------------------------------

    def _get_session(self):
        """Инициализировать requests.Session (lazy)."""
        if self._session is None:
            _validate_credentials(self.client_id, self.api_key)
            try:
                import requests
                self._session = requests.Session()
                self._session.headers.update(
                    {
                        "Client-Id": self.client_id,
                        "Api-Key": self.api_key,
                        "Content-Type": "application/json",
                    }
                )
            except ImportError:
                raise OzonAPIError("Библиотека 'requests' не установлена.")
        return self._session

    def _post(self, path: str, payload: dict) -> dict:
        """Выполнить POST-запрос к Ozon API."""
        if self.mock_mode:
            raise OzonAPIError("mock_mode=True, реальные запросы отключены")
        session = self._get_session()
        url = self.BASE_URL + path
        try:
            resp = session.post(url, json=payload, timeout=30)
        except Exception as e:
            raise OzonAPIError(f"Сетевая ошибка: {e}")
        if resp.status_code != 200:
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            raise OzonAPIError(
                f"HTTP {resp.status_code}: {body}", status_code=resp.status_code, response=body
            )
        return resp.json()

    # ------------------------------------------------------------------
    # Публичные методы API
    # ------------------------------------------------------------------

    def list_unfulfilled_postings(
        self,
        limit: int = 50,
        offset: int = 0,
        with_analytics_data: bool = False,
    ) -> List[Dict]:
        """
        POST /v3/posting/fbs/unfulfilled/list
        Возвращает список необработанных FBS-отправлений.
        """
        if self.mock_mode:
            logger.info("[MOCK] list_unfulfilled_postings → %d записей", len(MOCK_POSTINGS))
            return list(MOCK_POSTINGS)

        payload = {
            "dir": "asc",
            "filter": {
                "cutoff_from": (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z"),
                "cutoff_to": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%dT23:59:59Z"),
                "status": "awaiting_packaging",
            },
            "limit": limit,
            "offset": offset,
            "with": {
                "analytics_data": with_analytics_data,
                "barcodes": True,
                "financial_data": False,
                "product_exemplars": False,
                "related_postings": False,
                "translit": False,
            },
        }
        data = self._post("/v3/posting/fbs/unfulfilled/list", payload)
        # tolerant parsing: result может быть в разных уровнях
        result = data.get("result", data)
        postings = result.get("postings", result) if isinstance(result, dict) else result
        return postings if isinstance(postings, list) else []

    def get_posting(self, posting_number: str) -> Optional[Dict]:
        """
        POST /v3/posting/fbs/get
        Получить детали конкретного отправления.
        """
        if self.mock_mode:
            for p in MOCK_POSTINGS:
                if p["posting_number"] == posting_number:
                    logger.info("[MOCK] get_posting(%s) → ok", posting_number)
                    return p
            logger.warning("[MOCK] get_posting(%s) → не найдено", posting_number)
            return None

        payload = {
            "posting_number": posting_number,
            "with": {
                "analytics_data": False,
                "barcodes": True,
                "financial_data": False,
                "product_exemplars": False,
                "related_postings": False,
                "translit": False,
            },
        }
        data = self._post("/v3/posting/fbs/get", payload)
        result = data.get("result", data)
        return result if isinstance(result, dict) else None

    def get_package_label(self, posting_numbers: List[str]) -> Optional[bytes]:
        """
        POST /v2/posting/fbs/package-label
        Получить маршрутную этикетку (PDF) от Ozon.
        Возвращает байты PDF или None.
        """
        if self.mock_mode:
            logger.info("[MOCK] get_package_label → возвращаю stub PDF")
            return _mock_stub_pdf(posting_numbers)

        payload = {"posting_number": posting_numbers}
        data = self._post("/v2/posting/fbs/package-label", payload)

        # Tolerant parsing: PDF может быть в разных полях
        if isinstance(data, bytes):
            return data

        # Поле content (base64)
        for key in ("content", "label", "pdf", "data", "file"):
            val = data.get(key)
            if val:
                if isinstance(val, bytes):
                    return val
                if isinstance(val, str):
                    try:
                        return base64.b64decode(val)
                    except Exception:
                        pass

        # Fallback: URL
        url = data.get("url") or data.get("link")
        if url:
            try:
                import requests
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    return resp.content
            except Exception as e:
                logger.error("Не удалось загрузить маршрутную этикетку по URL: %s", e)

        logger.error("get_package_label: не удалось извлечь PDF из ответа: %s", list(data.keys()))
        return None

    def product_info_list(self, offer_ids: List[str] = None, skus: List[int] = None) -> List[Dict]:
        """
        POST /v3/product/info/list
        Получить информацию о товарах.
        """
        if self.mock_mode:
            logger.info("[MOCK] product_info_list → mock items")
            return []

        payload: dict = {}
        if offer_ids:
            payload["offer_id"] = offer_ids
        if skus:
            payload["sku"] = skus
        if not payload:
            return []

        data = self._post("/v3/product/info/list", payload)
        result = data.get("result", data)
        items = result.get("items", result) if isinstance(result, dict) else result
        return items if isinstance(items, list) else []

    def product_attributes(self, filter_: dict = None, limit: int = 100) -> List[Dict]:
        """
        POST /v4/product/info/attributes
        Получить атрибуты товаров.
        """
        if self.mock_mode:
            return []

        payload = {
            "filter": filter_ or {},
            "limit": limit,
            "sort_dir": "asc",
        }
        data = self._post("/v4/product/info/attributes", payload)
        result = data.get("result", data)
        return result if isinstance(result, list) else []

    # ------------------------------------------------------------------
    # Нормализация данных
    # ------------------------------------------------------------------

    def normalize_posting(self, raw: Dict) -> List[Dict]:
        """
        Нормализовать «сырое» отправление в список словарей,
        пригодных для создания LabelContext (по одному на товар/позицию).
        """
        posting_number = raw.get("posting_number", "")
        order_number = raw.get("order_number", "")
        products = raw.get("products", [])
        contexts = []
        for prod in products:
            # Артикул: сначала поле article, потом offer_id
            article = (
                prod.get("article")
                or prod.get("offer_id")
                or ""
            )
            # Штрихкод: может быть строкой или списком
            barcode_raw = prod.get("barcode") or prod.get("barcodes") or ""
            if isinstance(barcode_raw, list):
                barcode = barcode_raw[0] if barcode_raw else ""
            else:
                barcode = str(barcode_raw)

            ctx_dict = {
                "posting_number": posting_number,
                "order_number": order_number,
                "product_name": prod.get("name", ""),
                "article": article,
                "offer_id": prod.get("offer_id", ""),
                "sku": str(prod.get("sku", "")),
                "barcode": barcode,
                "manufacturer_part_number": prod.get("manufacturer_part_number", ""),
                "quantity": int(prod.get("quantity", 1)),
            }
            contexts.append(ctx_dict)
        return contexts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_stub_pdf(posting_numbers: List[str]) -> bytes:
    """Генерирует минимальный stub PDF для mock-режима."""
    text = ", ".join(posting_numbers)
    content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>>>endobj
4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
5 0 obj<</Length 80>>
stream
BT /F1 14 Tf 50 750 Td (MOCK Маршрутная этикетка) Tj 0 -20 Td ({text}) Tj ET
endstream
endobj
xref
0 6
0000000000 65535 f 
trailer<</Size 6/Root 1 0 R>>
startxref 9
%%EOF"""
    return content.encode("latin-1", errors="replace")
