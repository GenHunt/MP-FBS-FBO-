"""
Shipments tab - displays and manages FBS postings from Ozon
"""
import logging
from typing import List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QProgressBar,
    QHeaderView, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor

from src.models.shipment import Shipment

logger = logging.getLogger(__name__)

# Table column indices
COL_SELECT = 0
COL_POSTING = 1
COL_ORDER = 2
COL_STATUS = 3
COL_CREATED = 4
COL_ITEMS = 5


class LoadShipmentsThread(QThread):
    """Background thread for loading shipments from Ozon API"""
    shipments_loaded = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client

    def run(self):
        try:
            shipments = self.api_client.get_postings()
            self.shipments_loaded.emit(shipments)
        except Exception as e:
            self.error.emit(str(e))


class ShipmentsTab(QWidget):
    """Tab showing FBS postings with selection for printing"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._shipments: List[Shipment] = []
        self._load_thread = None

        self._create_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _create_ui(self) -> None:
        layout = QVBoxLayout()

        # Toolbar
        toolbar = QHBoxLayout()

        self.refresh_btn = QPushButton("Обновить список заказов")
        self.refresh_btn.clicked.connect(self.load_shipments)
        toolbar.addWidget(self.refresh_btn)

        self.select_all_btn = QPushButton("Выбрать все")
        self.select_all_btn.clicked.connect(self.select_all)
        toolbar.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Снять выделение")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        toolbar.addWidget(self.deselect_all_btn)

        toolbar.addStretch()

        self.count_label = QLabel("Заказов: 0")
        toolbar.addWidget(self.count_label)

        layout.addLayout(toolbar)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # indeterminate
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Нажмите 'Обновить' для загрузки заказов")
        layout.addWidget(self.status_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Выбрать", "Номер отправления", "Номер заказа",
            "Статус", "Дата создания", "Товаров",
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            COL_POSTING, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_shipments(self) -> None:
        """Load shipments from the API (non-blocking)."""
        if not self.main_window.is_connected():
            QMessageBox.warning(
                self, "Ошибка",
                "Пожалуйста, сначала подключитесь к Ozon API"
            )
            return

        self.progress_bar.setVisible(True)
        self.refresh_btn.setEnabled(False)
        self.status_label.setText("Загрузка заказов...")

        self._load_thread = LoadShipmentsThread(self.main_window.get_api_client())
        self._load_thread.shipments_loaded.connect(self._on_shipments_loaded)
        self._load_thread.error.connect(self._on_load_error)
        self._load_thread.start()

    def _on_shipments_loaded(self, shipments: list) -> None:
        self._shipments = shipments
        self._populate_table()
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Загружено {len(shipments)} заказов")
        self.count_label.setText(f"Заказов: {len(shipments)}")

        # Persist to DB for analytics
        try:
            from src.database import Database
            db = Database()
            for s in shipments:
                db.save_shipment(s)
        except Exception as e:
            logger.warning(f"Failed to save shipments to DB: {e}")

    def _on_load_error(self, error: str) -> None:
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Ошибка загрузки: {error}")
        QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить заказы:\n{error}")

    # ------------------------------------------------------------------
    # Table population
    # ------------------------------------------------------------------

    def _populate_table(self) -> None:
        self.table.setRowCount(0)
        for shipment in self._shipments:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Checkbox
            cb = QTableWidgetItem()
            cb.setCheckState(Qt.CheckState.Unchecked)
            cb.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, COL_SELECT, cb)

            self.table.setItem(row, COL_POSTING, QTableWidgetItem(shipment.shipment_id))
            self.table.setItem(row, COL_ORDER, QTableWidgetItem(shipment.order_id))
            self.table.setItem(row, COL_STATUS, QTableWidgetItem(shipment.status))
            self.table.setItem(row, COL_CREATED, QTableWidgetItem(shipment.created_at))
            self.table.setItem(row, COL_ITEMS, QTableWidgetItem(str(len(shipment.items))))

        self.table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------

    def select_all(self) -> None:
        """Check all shipments in the table."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_SELECT)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def deselect_all(self) -> None:
        """Uncheck all shipments in the table."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_SELECT)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def get_selected_shipments(self) -> List[Shipment]:
        """Return shipments whose checkbox is checked."""
        selected = []
        for row in range(self.table.rowCount()):
            cb = self.table.item(row, COL_SELECT)
            if cb and cb.checkState() == Qt.CheckState.Checked:
                posting_item = self.table.item(row, COL_POSTING)
                if posting_item:
                    posting_number = posting_item.text()
                    for s in self._shipments:
                        if s.shipment_id == posting_number:
                            selected.append(s)
                            break
        return selected
