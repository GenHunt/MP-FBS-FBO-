"""
Analytics dashboard tab for order timing insights
"""
import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt6.QtGui import QPainter, QColor

from src.order_timing_analytics import OrderTimingAnalytics
from src.database import Database

logger = logging.getLogger(__name__)


class AnalyticsThread(QThread):
    """Thread for loading analytics data"""
    data_loaded = pyqtSignal(dict)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, analytics: OrderTimingAnalytics):
        super().__init__()
        self.analytics = analytics
    
    def run(self):
        try:
            data = {
                'hourly': self.analytics.get_hourly_distribution(),
                'daily': self.analytics.get_daily_pattern(),
                'optimal_times': self.analytics.get_optimal_shipment_times(),
                'predictions': self.analytics.predict_busy_periods(),
                'efficiency': self.analytics.get_efficiency_score(),
            }
            self.data_loaded.emit(data)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()


class AnalyticsTab(QWidget):
    """Tab for order timing analytics and optimization"""
    
    def __init__(self, main_window):
        """Initialize analytics tab"""
        super().__init__()
        self.main_window = main_window
        self.analytics = OrderTimingAnalytics(Database())
        self.analytics_thread = None
        self.current_data = {}
        
        self.create_ui()
    
    def create_ui(self) -> None:
        """Create UI"""
        layout = QVBoxLayout()
        
        # Top controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Период анализа:"))
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["7 дней", "30 дней", "60 дней", "90 дней"])
        self.period_combo.currentTextChanged.connect(self.on_period_changed)
        controls_layout.addWidget(self.period_combo)
        
        self.refresh_btn = QPushButton("🔄 Обновить аналитику")
        self.refresh_btn.clicked.connect(self.load_analytics)
        controls_layout.addWidget(self.refresh_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Tab widget for different views
        self.analytics_tabs = QTabWidget()
        
        # 1. Summary statistics tab
        summary_tab = self.create_summary_tab()
        self.analytics_tabs.addTab(summary_tab, "📊 Статистика")
        
        # 2. Hourly distribution tab
        hourly_tab = self.create_hourly_tab()
        self.analytics_tabs.addTab(hourly_tab, "⏰ По часам")
        
        # 3. Daily pattern tab
        daily_tab = self.create_daily_tab()
        self.analytics_tabs.addTab(daily_tab, "📅 По дням")
        
        # 4. Recommendations tab
        recommendations_tab = self.create_recommendations_tab()
        self.analytics_tabs.addTab(recommendations_tab, "💡 Рекомендации")
        
        # 5. Predictions tab
        predictions_tab = self.create_predictions_tab()
        self.analytics_tabs.addTab(predictions_tab, "🔮 Прогнозы")
        
        layout.addWidget(self.analytics_tabs)
        
        self.setLayout(layout)
        
        # Load initial data
        self.load_analytics()
    
    def create_summary_tab(self) -> QWidget:
        """Create summary statistics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Efficiency score
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("Коэффициент эффективности:"))
        self.efficiency_label = QLabel("--")
        self.efficiency_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        score_layout.addWidget(self.efficiency_label)
        score_layout.addStretch()
        layout.addLayout(score_layout)
        
        # On-time rate
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Доля вовремя обработанных:"))
        self.ontime_label = QLabel("-- %")
        self.ontime_label.setStyleSheet("font-size: 16px; color: green;")
        rate_layout.addWidget(self.ontime_label)
        rate_layout.addStretch()
        layout.addLayout(rate_layout)
        
        # Average processing time
        proc_layout = QHBoxLayout()
        proc_layout.addWidget(QLabel("Среднее время обработки:"))
        self.processing_label = QLabel("-- часов")
        self.processing_label.setStyleSheet("font-size: 16px;")
        proc_layout.addWidget(self.processing_label)
        proc_layout.addStretch()
        layout.addLayout(proc_layout)
        
        # Summary table
        layout.addWidget(QLabel("Обзор по дням недели:"))
        
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(5)
        self.summary_table.setHorizontalHeaderLabels([
            "День недели", "Заказов", "Товаров", "Макс часы", "Статус"
        ])
        self.summary_table.setMaximumHeight(300)
        layout.addWidget(self.summary_table)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_hourly_tab(self) -> QWidget:
        """Create hourly distribution tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Распределение заказов по часам дня:"))
        
        self.hourly_table = QTableWidget()
        self.hourly_table.setColumnCount(4)
        self.hourly_table.setHorizontalHeaderLabels([
            "Час", "Заказов", "Товаров", "Пиковое время"
        ])
        layout.addWidget(self.hourly_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_daily_tab(self) -> QWidget:
        """Create daily pattern tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Паттерн по дням недели:"))
        
        self.daily_table = QTableWidget()
        self.daily_table.setColumnCount(5)
        self.daily_table.setHorizontalHeaderLabels([
            "День", "Заказов", "Среднее товаров", "Пиковые часы", "Загруженность"
        ])
        layout.addWidget(self.daily_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_recommendations_tab(self) -> QWidget:
        """Create recommendations tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Оптимальные окна отгрузки по дням:"))
        
        self.recommendations_table = QTableWidget()
        self.recommendations_table.setColumnCount(3)
        self.recommendations_table.setHorizontalHeaderLabels([
            "День недели", "Окна отгрузки", "Рекомендация"
        ])
        self.recommendations_table.setMaximumHeight(400)
        layout.addWidget(self.recommendations_table)
        
        layout.addWidget(QLabel("\n💡 Советы по оптимизации:"))
        
        self.tips_label = QLabel()
        self.tips_label.setWordWrap(True)
        self.tips_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.tips_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_predictions_tab(self) -> QWidget:
        """Create predictions tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Прогноз загруженности на неделю:"))
        
        self.predictions_table = QTableWidget()
        self.predictions_table.setColumnCount(5)
        self.predictions_table.setHorizontalHeaderLabels([
            "День", "Дата", "Ожидаемые заказы", "Пиковые часы", "Уверенность"
        ])
        self.predictions_table.setMaximumHeight(300)
        layout.addWidget(self.predictions_table)
        
        layout.addWidget(QLabel("\n📊 Риск задержек:"))
        
        risk_layout = QHBoxLayout()
        risk_layout.addWidget(QLabel("Текущее состояние:"))
        self.risk_label = QLabel("--")
        self.risk_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        risk_layout.addWidget(self.risk_label)
        risk_layout.addStretch()
        layout.addLayout(risk_layout)
        
        layout.addWidget(QLabel("Рекомендация:"))
        self.risk_recommendation = QLabel()
        self.risk_recommendation.setWordWrap(True)
        layout.addWidget(self.risk_recommendation)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def on_period_changed(self) -> None:
        """Handle period change"""
        self.load_analytics()
    
    def load_analytics(self) -> None:
        """Load analytics data"""
        self.progress_bar.setVisible(True)
        self.refresh_btn.setEnabled(False)
        
        self.analytics_thread = AnalyticsThread(self.analytics)
        self.analytics_thread.data_loaded.connect(self.on_data_loaded)
        self.analytics_thread.finished.connect(self.on_load_finished)
        self.analytics_thread.error.connect(self.on_load_error)
        self.analytics_thread.start()
    
    def on_data_loaded(self, data: dict) -> None:
        """Handle loaded analytics data"""
        self.current_data = data
        self.update_summary_tab()
        self.update_hourly_tab()
        self.update_daily_tab()
        self.update_recommendations_tab()
        self.update_predictions_tab()
    
    def on_load_finished(self) -> None:
        """Handle load finished"""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
    
    def on_load_error(self, error: str) -> None:
        """Handle load error"""
        QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить аналитику: {error}")
    
    def update_summary_tab(self) -> None:
        """Update summary tab with data"""
        if 'efficiency' in self.current_data:
            eff = self.current_data['efficiency']
            self.efficiency_label.setText(f"{eff.get('efficiency_score', 0):.1f}/100")
            self.ontime_label.setText(f"{eff.get('on_time_rate', 0):.1f} %")
            self.processing_label.setText(f"{eff.get('average_processing_hours', 0):.1f} часов")
        
        if 'daily' in self.current_data:
            daily = self.current_data['daily']
            self.summary_table.setRowCount(len(daily))
            
            for row, (day, stats) in enumerate(daily.items()):
                self.summary_table.setItem(row, 0, QTableWidgetItem(day))
                self.summary_table.setItem(row, 1, QTableWidgetItem(str(stats['order_count'])))
                self.summary_table.setItem(row, 2, QTableWidgetItem(str(stats['total_items'])))
                
                peak_hours = ', '.join(map(str, stats['peak_hours']))
                self.summary_table.setItem(row, 3, QTableWidgetItem(peak_hours or "Нет"))
                
                status = "Загружен" if stats['busiest'] else "Нормально"
                self.summary_table.setItem(row, 4, QTableWidgetItem(status))
    
    def update_hourly_tab(self) -> None:
        """Update hourly tab with data"""
        if 'hourly' in self.current_data:
            hourly = self.current_data['hourly']
            self.hourly_table.setRowCount(24)
            
            for hour in range(24):
                if hour in hourly:
                    stats = hourly[hour]
                    self.hourly_table.setItem(hour, 0, QTableWidgetItem(f"{hour:02d}:00"))
                    self.hourly_table.setItem(hour, 1, QTableWidgetItem(str(stats['order_count'])))
                    self.hourly_table.setItem(hour, 2, QTableWidgetItem(str(stats['total_items'])))
                    
                    peak_marker = "🔴 ПИКОВОЕ" if stats['peak'] else ""
                    self.hourly_table.setItem(hour, 3, QTableWidgetItem(peak_marker))
                else:
                    self.hourly_table.setItem(hour, 0, QTableWidgetItem(f"{hour:02d}:00"))
                    self.hourly_table.setItem(hour, 1, QTableWidgetItem("0"))
                    self.hourly_table.setItem(hour, 2, QTableWidgetItem("0"))
                    self.hourly_table.setItem(hour, 3, QTableWidgetItem(""))
    
    def update_daily_tab(self) -> None:
        """Update daily tab with data"""
        if 'daily' in self.current_data:
            daily = self.current_data['daily']
            self.daily_table.setRowCount(len(daily))
            
            for row, (day, stats) in enumerate(daily.items()):
                self.daily_table.setItem(row, 0, QTableWidgetItem(day))
                self.daily_table.setItem(row, 1, QTableWidgetItem(str(stats['order_count'])))
                self.daily_table.setItem(row, 2, QTableWidgetItem(f"{stats['avg_items_per_order']:.1f}"))
                
                peak_hours = ', '.join(map(str, stats['peak_hours']))
                self.daily_table.setItem(row, 3, QTableWidgetItem(peak_hours or "Нет"))
                
                load = "⚠️ ВЫСОКАЯ" if stats['busiest'] else "✓ Нормальная"
                self.daily_table.setItem(row, 4, QTableWidgetItem(load))
    
    def update_recommendations_tab(self) -> None:
        """Update recommendations tab with data"""
        if 'optimal_times' in self.current_data:
            optimal = self.current_data['optimal_times']
            self.recommendations_table.setRowCount(len(optimal))
            
            for row, (day, windows) in enumerate(optimal.items()):
                self.recommendations_table.setItem(row, 0, QTableWidgetItem(day))
                
                windows_str = ", ".join([f"{w[0]:02d}:00-{w[1]:02d}:00" for w in windows])
                self.recommendations_table.setItem(row, 1, QTableWidgetItem(windows_str))
                
                if 'daily' in self.current_data:
                    daily = self.current_data['daily']
                    if day in daily and daily[day]['busiest']:
                        rec = "🔴 Добавить ресурсы"
                    else:
                        rec = "✓ Нормальная нагрузка"
                    self.recommendations_table.setItem(row, 2, QTableWidgetItem(rec))
            
            tips = """
            • Отгружайте товары в оптимальные окна для ускорения доставки
            • Пиковые часы требуют больше ресурсов и внимания
            • На тихие периоды можно запланировать техническое обслуживание
            • Используйте прогнозы для планирования штата
            """
            self.tips_label.setText(tips)
    
    def update_predictions_tab(self) -> None:
        """Update predictions tab with data"""
        if 'predictions' in self.current_data:
            predictions = self.current_data['predictions']
            self.predictions_table.setRowCount(len(predictions))
            
            for row, pred in enumerate(predictions):
                self.predictions_table.setItem(row, 0, QTableWidgetItem(pred['day']))
                self.predictions_table.setItem(row, 1, QTableWidgetItem(pred['date']))
                self.predictions_table.setItem(row, 2, QTableWidgetItem(str(pred['predicted_order_count'])))
                
                peak_hours = ', '.join(map(str, pred['peak_hours']))
                self.predictions_table.setItem(row, 3, QTableWidgetItem(peak_hours))
                
                confidence = f"{pred['confidence']:.0f}%"
                self.predictions_table.setItem(row, 4, QTableWidgetItem(confidence))
        
        # Update current risk assessment
        current_hour = datetime.now().hour
        if self.main_window.shipments_tab:
            pending = len(self.main_window.shipments_tab.get_selected_shipments())
            risk = self.analytics.get_delay_risk(current_hour, pending)
            
            risk_colors = {'low': 'green', 'medium': 'orange', 'high': 'red'}
            risk_text = {'low': '✓ Низкий', 'medium': '⚠️ Средний', 'high': '🔴 Высокий'}
            
            self.risk_label.setText(risk_text.get(risk['risk_level'], 'Неизвестно'))
            self.risk_label.setStyleSheet(f"color: {risk_colors.get(risk['risk_level'], 'black')};")
            self.risk_recommendation.setText(risk.get('recommendation', ''))
