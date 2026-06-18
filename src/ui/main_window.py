"""
Main application window
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QCheckBox, QRadioButton, QButtonGroup, QMessageBox, QFileDialog,
    QProgressBar, QTextEdit, QSplitter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

from src.api import OzonAPIClient
from src.templates import TemplateManager
from src.models.template import Template
from src.ui.tabs.shipments_tab import ShipmentsTab
from src.ui.tabs.print_tab import PrintTab
from src.ui.tabs.template_editor_tab import TemplateEditorTab
from src.ui.tabs.logs_tab import LogsTab
from src.ui.tabs.settings_tab import SettingsTab
from src.ui.tabs.analytics_tab import AnalyticsTab

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        """Initialize main window"""
        super().__init__()
        self.setWindowTitle("Ozon FBS Label Printer v1.0 - С аналитикой отгрузок")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
        self.api_client = None
        self.template_manager = TemplateManager()
        self.current_shipments = []
        self.current_template = None
        
        # Create UI
        self.create_ui()
        
        logger.info("Main window initialized")
    
    def create_ui(self) -> None:
        """Create user interface"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Top panel for API credentials
        top_panel = self.create_top_panel()
        main_layout.addLayout(top_panel)
        
        # Tab widget
        tab_widget = QTabWidget()
        
        # Create tabs
        self.shipments_tab = ShipmentsTab(self)
        self.print_tab = PrintTab(self)
        self.template_editor_tab = TemplateEditorTab(self)
        self.analytics_tab = AnalyticsTab(self)
        self.logs_tab = LogsTab(self)
        self.settings_tab = SettingsTab(self)
        
        # Add tabs
        tab_widget.addTab(self.shipments_tab, "📦 Заказы")
        tab_widget.addTab(self.print_tab, "🖨️ Печать")
        tab_widget.addTab(self.template_editor_tab, "✏️ Редактор шаблонов")
        tab_widget.addTab(self.analytics_tab, "📊 Аналитика")
        tab_widget.addTab(self.logs_tab, "📋 Логи")
        tab_widget.addTab(self.settings_tab, "⚙️ Настройки")
        
        main_layout.addWidget(tab_widget)
        
        central_widget.setLayout(main_layout)
    
    def create_top_panel(self) -> QHBoxLayout:
        """Create top panel with API credentials"""
        layout = QHBoxLayout()
        
        # Client ID
        layout.addWidget(QLabel("Client ID:"))
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("Введите Client ID")
        self.client_id_input.setMaximumWidth(200)
        layout.addWidget(self.client_id_input)
        
        # API Key
        layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Введите API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setMaximumWidth(200)
        layout.addWidget(self.api_key_input)
        
        # Connection button
        self.connect_btn = QPushButton("✓ Подключиться")
        self.connect_btn.clicked.connect(self.connect_to_api)
        self.connect_btn.setMaximumWidth(150)
        layout.addWidget(self.connect_btn)
        
        # Status label
        self.status_label = QLabel("❌ Не подключено")
        self.status_label.setMaximumWidth(200)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        return layout
    
    def connect_to_api(self) -> None:
        """Connect to Ozon API"""
        client_id = self.client_id_input.text().strip()
        api_key = self.api_key_input.text().strip()
        
        if not client_id or not api_key:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите Client ID и API Key")
            return
        
        try:
            self.api_client = OzonAPIClient(client_id, api_key)
            
            # Test connection
            if self.api_client.test_connection():
                self.status_label.setText("✅ Подключено к Ozon")
                self.status_label.setStyleSheet("color: green;")
                QMessageBox.information(self, "Успех", "Успешно подключено к Ozon API")
                
                # Load shipments
                self.shipments_tab.load_shipments()
            else:
                raise Exception("Failed to connect to API")
        
        except Exception as e:
            self.status_label.setText("❌ Ошибка подключения")
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться: {str(e)}")
            logger.error(f"Failed to connect to API: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to API"""
        return self.api_client is not None and self.status_label.text().startswith("✅")
    
    def get_api_client(self) -> OzonAPIClient:
        """Get API client"""
        return self.api_client
    
    def get_template_manager(self) -> TemplateManager:
        """Get template manager"""
        return self.template_manager
    
    def update_current_shipments(self, shipments) -> None:
        """Update current shipments"""
        self.current_shipments = shipments
    
    def update_current_template(self, template: Template) -> None:
        """Update current template"""
        self.current_template = template
