"""
Shipment and ShipmentItem data models
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ShipmentItem:
    """Represents a single product line in a shipment"""
    sku: int
    offer_id: str
    product_name: str
    quantity: int
    price: str = ''
    barcode: str = ''
    article: str = ''
    manufacturer_part_number: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template variable substitution"""
        return {
            'sku': str(self.sku),
            'offer_id': self.offer_id,
            'product_name': self.product_name,
            'quantity': str(self.quantity),
            'price': self.price,
            'barcode': self.barcode,
            'article': self.article or self.offer_id,
            'manufacturer_part_number': self.manufacturer_part_number,
        }

    def __repr__(self) -> str:
        return f"ShipmentItem(sku={self.sku}, offer_id={self.offer_id!r}, qty={self.quantity})"


@dataclass
class Shipment:
    """Represents an FBS shipment (posting)"""
    shipment_id: str
    order_id: str
    status: str
    created_at: str
    items: List[ShipmentItem] = field(default_factory=list)
    label_data: Optional[bytes] = None
    in_process_at: str = ''
    shipment_date: str = ''

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'shipment_id': self.shipment_id,
            'order_id': self.order_id,
            'status': self.status,
            'created_at': self.created_at,
            'in_process_at': self.in_process_at,
            'shipment_date': self.shipment_date,
        }

    def total_items(self) -> int:
        """Return total number of product units"""
        return sum(item.quantity for item in self.items)

    def __repr__(self) -> str:
        return f"Shipment(id={self.shipment_id!r}, items={len(self.items)})"
