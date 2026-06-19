"""
SQLite database helper
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class Database:
    """Manages the application SQLite database"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            import config
            db_path = config.DB_PATH

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_schema(self) -> None:
        """Create tables if they do not exist."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS shipments (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    shipment_id     TEXT NOT NULL UNIQUE,
                    order_id        TEXT,
                    status          TEXT,
                    created_at      TEXT,
                    in_process_at   TEXT,
                    shipment_date   TEXT,
                    recorded_at     DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS shipment_items (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    shipment_id     TEXT NOT NULL,
                    sku             INTEGER,
                    offer_id        TEXT,
                    product_name    TEXT,
                    quantity        INTEGER,
                    price           TEXT,
                    barcode         TEXT,
                    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
                );

                CREATE TABLE IF NOT EXISTS print_log (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    shipment_id     TEXT,
                    print_type      TEXT,
                    template_id     TEXT,
                    printer_name    TEXT,
                    success         INTEGER DEFAULT 1,
                    printed_at      DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_shipments_created
                    ON shipments(created_at);
                CREATE INDEX IF NOT EXISTS idx_print_log_printed_at
                    ON print_log(printed_at);
                """
            )
        logger.debug("Database schema initialized")

    # ------------------------------------------------------------------
    # Connection helper
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Shipments
    # ------------------------------------------------------------------

    def save_shipment(self, shipment) -> bool:
        """Persist a Shipment (and its items) to the database."""
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO shipments
                        (shipment_id, order_id, status, created_at,
                         in_process_at, shipment_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        shipment.shipment_id,
                        shipment.order_id,
                        shipment.status,
                        shipment.created_at,
                        shipment.in_process_at,
                        shipment.shipment_date,
                    ),
                )
                for item in shipment.items:
                    conn.execute(
                        """
                        INSERT INTO shipment_items
                            (shipment_id, sku, offer_id, product_name,
                             quantity, price, barcode)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            shipment.shipment_id,
                            item.sku,
                            item.offer_id,
                            item.product_name,
                            item.quantity,
                            item.price,
                            item.barcode,
                        ),
                    )
            return True
        except Exception as e:
            logger.error(f"Failed to save shipment {shipment.shipment_id}: {e}")
            return False

    def get_shipments(
        self, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Return shipment rows recorded within the last *days* days."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT * FROM shipments
                    WHERE recorded_at >= datetime('now', ?)
                    ORDER BY created_at DESC
                    """,
                    (f'-{days} days',),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch shipments: {e}")
            return []

    def get_shipment_items(self, shipment_id: str) -> List[Dict[str, Any]]:
        """Return all items for a given shipment."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM shipment_items WHERE shipment_id = ?",
                    (shipment_id,),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch items for {shipment_id}: {e}")
            return []

    # ------------------------------------------------------------------
    # Print log
    # ------------------------------------------------------------------

    def log_print(
        self,
        shipment_id: str,
        print_type: str,
        template_id: str,
        printer_name: str,
        success: bool = True,
    ) -> None:
        """Record a print event."""
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO print_log
                        (shipment_id, print_type, template_id, printer_name, success)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (shipment_id, print_type, template_id, printer_name, int(success)),
                )
        except Exception as e:
            logger.error(f"Failed to log print: {e}")

    def get_print_log(self, days: int = 30) -> List[Dict[str, Any]]:
        """Return print log entries for the last *days* days."""
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT * FROM print_log
                    WHERE printed_at >= datetime('now', ?)
                    ORDER BY printed_at DESC
                    """,
                    (f'-{days} days',),
                ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch print log: {e}")
            return []
