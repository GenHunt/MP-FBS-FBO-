"""
Модель данных для генерации этикетки.
LabelContext — нормализованное представление одного отправления/товара.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class LabelContext:
    """Контекст для подстановки переменных в шаблон этикетки."""

    # Идентификаторы отправления
    posting_number: str = ""
    order_number: str = ""

    # Товар
    product_name: str = ""
    article: str = ""          # Артикул карточки Ozon
    offer_id: str = ""         # offer_id продавца (fallback для article)
    sku: str = ""              # SKU (Ozon internal id)
    barcode: str = ""          # Штрихкод (EAN/GTIN)
    manufacturer_part_number: str = ""  # Партномер (MPN)

    # Количество и упаковка
    quantity: int = 1

    # Дата/время (заполняется автоматически при генерации)
    date: str = ""
    time: str = ""

    # Маршрутная этикетка (PDF/bytes от Ozon)
    route_label_pdf: Optional[bytes] = field(default=None, repr=False)

    def __post_init__(self):
        now = datetime.now()
        if not self.date:
            self.date = now.strftime("%d.%m.%Y")
        if not self.time:
            self.time = now.strftime("%H:%M")
        # Fallback: если article пустой — используем offer_id
        if not self.article and self.offer_id:
            self.article = self.offer_id

    def get_variable(self, name: str) -> str:
        """Получить значение переменной по имени для подстановки в шаблон."""
        mapping = {
            "article": self.article or self.offer_id or "",
            "product_name": self.product_name,
            "barcode": self.barcode,
            "manufacturer_part_number": self.manufacturer_part_number,
            "offer_id": self.offer_id,
            "sku": self.sku,
            "posting_number": self.posting_number,
            "order_number": self.order_number,
            "quantity": str(self.quantity),
            "date": self.date,
            "time": self.time,
        }
        return mapping.get(name, "")

    @classmethod
    def from_dict(cls, data: dict) -> "LabelContext":
        """Создать контекст из словаря (tolerant parsing)."""
        return cls(
            posting_number=str(data.get("posting_number", "")),
            order_number=str(data.get("order_number", "")),
            product_name=str(data.get("product_name", "")),
            article=str(data.get("article", "")),
            offer_id=str(data.get("offer_id", "")),
            sku=str(data.get("sku", "")),
            barcode=str(data.get("barcode", "")),
            manufacturer_part_number=str(data.get("manufacturer_part_number", "")),
            quantity=int(data.get("quantity", 1)),
            date=str(data.get("date", "")),
            time=str(data.get("time", "")),
        )

    def to_dict(self) -> dict:
        return {
            "posting_number": self.posting_number,
            "order_number": self.order_number,
            "product_name": self.product_name,
            "article": self.article,
            "offer_id": self.offer_id,
            "sku": self.sku,
            "barcode": self.barcode,
            "manufacturer_part_number": self.manufacturer_part_number,
            "quantity": self.quantity,
            "date": self.date,
            "time": self.time,
        }
