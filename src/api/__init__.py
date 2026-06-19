"""
Ozon Seller API client
"""
import logging
from typing import List, Optional, Dict, Any

import requests

from src.models.shipment import Shipment, ShipmentItem

logger = logging.getLogger(__name__)

_API_BASE = 'https://api-seller.ozon.ru'


class OzonAPIClient:
    """Client for the Ozon Seller API"""

    def __init__(self, client_id: str, api_key: str, base_url: str = _API_BASE):
        self.client_id = client_id
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Client-Id': client_id,
            'Api-Key': api_key,
            'Content-Type': 'application/json',
        })

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    def test_connection(self) -> bool:
        """
        Test API credentials by fetching the warehouse list.

        Returns:
            True if the credentials are valid.

        Raises:
            Exception if connection fails.
        """
        try:
            response = self.session.post(
                f'{self.base_url}/v1/warehouse/list',
                json={},
                timeout=10,
            )
            if response.status_code == 200:
                logger.info("API connection test successful")
                return True
            elif response.status_code == 401:
                raise Exception("Invalid API credentials (401 Unauthorized)")
            else:
                raise Exception(
                    f"API returned status {response.status_code}: {response.text}"
                )
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Network error: {e}") from e
        except requests.exceptions.Timeout:
            raise Exception("Connection timed out")

    # ------------------------------------------------------------------
    # Postings (shipments)
    # ------------------------------------------------------------------

    def get_postings(
        self,
        status: str = 'awaiting_deliver',
        limit: int = 100,
        offset: int = 0,
    ) -> List[Shipment]:
        """
        Fetch FBS postings from Ozon.

        Args:
            status: Posting status filter.
            limit:  Max items per request.
            offset: Pagination offset.

        Returns:
            List of Shipment objects.
        """
        payload = {
            'dir': 'ASC',
            'filter': {
                'status': status,
            },
            'limit': limit,
            'offset': offset,
            'with': {
                'analytics_data': False,
                'financial_data': False,
            },
        }

        try:
            response = self.session.post(
                f'{self.base_url}/v3/posting/fbs/list',
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            postings = data.get('result', {}).get('postings', [])
            shipments = [self._parse_posting(p) for p in postings]
            logger.info(f"Fetched {len(shipments)} postings")
            return shipments

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching postings: {e}")
            raise Exception(f"Failed to fetch postings: {e}") from e
        except Exception as e:
            logger.error(f"Error fetching postings: {e}")
            raise

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def get_label(self, posting_numbers: List[str]) -> Optional[bytes]:
        """
        Fetch shipping label PDF for the given postings.

        Args:
            posting_numbers: List of posting numbers.

        Returns:
            PDF bytes or None on failure.
        """
        if not posting_numbers:
            return None

        try:
            response = self.session.post(
                f'{self.base_url}/v2/posting/fbs/package-label',
                json={'posting_number': posting_numbers},
                timeout=30,
            )
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'pdf' in content_type or 'octet' in content_type:
                return response.content

            # Some responses return base64-encoded PDF in JSON
            data = response.json()
            import base64
            content = data.get('content') or data.get('label')
            if content:
                return base64.b64decode(content)

            return response.content

        except Exception as e:
            logger.error(f"Error fetching label for {posting_numbers}: {e}")
            return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_posting(self, posting: Dict[str, Any]) -> Shipment:
        """Convert a raw API posting dict into a Shipment object."""
        items = []
        for product in posting.get('products', []):
            item = ShipmentItem(
                sku=product.get('sku', 0),
                offer_id=product.get('offer_id', ''),
                product_name=product.get('name', ''),
                quantity=product.get('quantity', 1),
                price=str(product.get('price', '')),
                barcode='',
                article=product.get('offer_id', ''),
                manufacturer_part_number=product.get(
                    'mandatory_mark', ['']
                )[0] if product.get('mandatory_mark') else '',
            )
            items.append(item)

        return Shipment(
            shipment_id=posting.get('posting_number', ''),
            order_id=str(posting.get('order_id', '')),
            status=posting.get('status', ''),
            created_at=posting.get('created_at', ''),
            in_process_at=posting.get('in_process_at', ''),
            shipment_date=posting.get('shipment_date', ''),
            items=items,
        )
