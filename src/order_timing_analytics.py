"""
Order timing analytics - tracks when orders arrive and helps
optimise shipment windows.
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

_DAYS_RU = {
    0: 'Понедельник',
    1: 'Вторник',
    2: 'Среда',
    3: 'Четверг',
    4: 'Пятница',
    5: 'Суббота',
    6: 'Воскресенье',
}


class OrderTimingAnalytics:
    """
    Analyses historical shipment data to surface actionable timing insights.
    """

    def __init__(self, database):
        """
        Args:
            database: Database instance used for reading shipment records.
        """
        self.db = database

    # ------------------------------------------------------------------
    # Public analysis methods
    # ------------------------------------------------------------------

    def get_hourly_distribution(self, days: int = 30) -> Dict[int, Dict[str, Any]]:
        """
        Return order counts grouped by hour of day.

        Returns:
            {hour: {'order_count': int, 'total_items': int, 'peak': bool}}
        """
        shipments = self.db.get_shipments(days=days)
        hourly: Dict[int, dict] = defaultdict(lambda: {'order_count': 0, 'total_items': 0})

        for s in shipments:
            try:
                dt = self._parse_dt(s.get('created_at', ''))
                if dt:
                    hour = dt.hour
                    hourly[hour]['order_count'] += 1
                    items = self.db.get_shipment_items(s['shipment_id'])
                    hourly[hour]['total_items'] += sum(
                        i.get('quantity', 1) for i in items
                    )
            except Exception:
                pass

        if not hourly:
            return {}

        max_orders = max(v['order_count'] for v in hourly.values()) or 1
        threshold = max_orders * 0.7

        result = {}
        for hour, stats in hourly.items():
            result[hour] = {
                'order_count': stats['order_count'],
                'total_items': stats['total_items'],
                'peak': stats['order_count'] >= threshold,
            }
        return result

    def get_daily_pattern(self, days: int = 30) -> Dict[str, Dict[str, Any]]:
        """
        Return order counts grouped by day of week.

        Returns:
            {day_name: {'order_count', 'total_items', 'avg_items_per_order',
                        'peak_hours', 'busiest'}}
        """
        shipments = self.db.get_shipments(days=days)
        daily: Dict[int, dict] = defaultdict(
            lambda: {'order_count': 0, 'total_items': 0, 'hours': []}
        )

        for s in shipments:
            try:
                dt = self._parse_dt(s.get('created_at', ''))
                if dt:
                    dow = dt.weekday()
                    daily[dow]['order_count'] += 1
                    items = self.db.get_shipment_items(s['shipment_id'])
                    daily[dow]['total_items'] += sum(
                        i.get('quantity', 1) for i in items
                    )
                    daily[dow]['hours'].append(dt.hour)
            except Exception:
                pass

        if not daily:
            return {}

        max_orders = max(v['order_count'] for v in daily.values()) or 1
        threshold = max_orders * 0.8

        result = {}
        for dow in sorted(daily.keys()):
            stats = daily[dow]
            hours = stats['hours']
            peak_hours = self._top_n_hours(hours, n=3) if hours else []
            result[_DAYS_RU[dow]] = {
                'order_count': stats['order_count'],
                'total_items': stats['total_items'],
                'avg_items_per_order': (
                    stats['total_items'] / stats['order_count']
                    if stats['order_count'] else 0
                ),
                'peak_hours': peak_hours,
                'busiest': stats['order_count'] >= threshold,
            }
        return result

    def get_optimal_shipment_times(
        self, days: int = 30
    ) -> Dict[str, List[List[int]]]:
        """
        Return low-traffic shipment windows per day of week.

        Returns:
            {day_name: [[start_hour, end_hour], ...]}
        """
        hourly = self.get_hourly_distribution(days=days)
        daily = self.get_daily_pattern(days=days)

        result = {}
        for day_name in daily.keys():
            # Recommend windows outside peak hours
            peak_hours = set(daily[day_name]['peak_hours'])
            windows = []
            window_start = None
            for hour in range(8, 22):
                if hour not in peak_hours:
                    if window_start is None:
                        window_start = hour
                else:
                    if window_start is not None:
                        windows.append([window_start, hour])
                        window_start = None
            if window_start is not None:
                windows.append([window_start, 22])

            result[day_name] = windows or [[9, 17]]
        return result

    def predict_busy_periods(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Predict the next 7 days' order volume based on historical weekday patterns.

        Returns:
            List of {day, date, predicted_order_count, peak_hours, confidence}
        """
        daily = self.get_daily_pattern(days=days)
        predictions = []
        today = datetime.now()

        for delta in range(7):
            future = today + timedelta(days=delta + 1)
            day_name = _DAYS_RU[future.weekday()]
            stats = daily.get(day_name, {})

            predictions.append({
                'day': day_name,
                'date': future.strftime('%d.%m.%Y'),
                'predicted_order_count': stats.get('order_count', 0),
                'peak_hours': stats.get('peak_hours', []),
                'confidence': 75.0 if stats.get('order_count', 0) > 0 else 30.0,
            })
        return predictions

    def get_efficiency_score(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate a simple efficiency score.

        Returns:
            {efficiency_score, on_time_rate, average_processing_hours}
        """
        shipments = self.db.get_shipments(days=days)
        if not shipments:
            return {
                'efficiency_score': 0.0,
                'on_time_rate': 0.0,
                'average_processing_hours': 0.0,
            }

        on_time = 0
        processing_times = []

        for s in shipments:
            created = self._parse_dt(s.get('created_at', ''))
            in_process = self._parse_dt(s.get('in_process_at', ''))
            if created and in_process and in_process > created:
                hours = (in_process - created).total_seconds() / 3600
                processing_times.append(hours)
                if hours <= 24:
                    on_time += 1

        total = len(shipments)
        on_time_rate = (on_time / total * 100) if total else 0.0
        avg_hours = (
            sum(processing_times) / len(processing_times)
            if processing_times else 0.0
        )

        # Score: 100 if everything on time and fast
        efficiency = min(100.0, on_time_rate * 0.7 + max(0, (24 - avg_hours) / 24 * 30))
        return {
            'efficiency_score': round(efficiency, 1),
            'on_time_rate': round(on_time_rate, 1),
            'average_processing_hours': round(avg_hours, 1),
        }

    def get_delay_risk(
        self, current_hour: int, pending_orders: int
    ) -> Dict[str, str]:
        """
        Assess delay risk for current conditions.

        Returns:
            {risk_level: 'low'|'medium'|'high', recommendation: str}
        """
        hourly = self.get_hourly_distribution(days=30)
        peak_hours = {h for h, s in hourly.items() if s.get('peak')}

        is_peak = current_hour in peak_hours
        many_pending = pending_orders > 20

        if is_peak and many_pending:
            return {
                'risk_level': 'high',
                'recommendation': (
                    'Пиковое время + много заказов. Рекомендуется привлечь '
                    'дополнительные ресурсы для ускорения отгрузки.'
                ),
            }
        elif is_peak or many_pending:
            return {
                'risk_level': 'medium',
                'recommendation': (
                    'Умеренная нагрузка. Следите за скоростью обработки.'
                ),
            }
        else:
            return {
                'risk_level': 'low',
                'recommendation': 'Нагрузка в норме. Продолжайте в обычном режиме.',
            }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_dt(value: str) -> Optional[datetime]:
        if not value:
            return None
        for fmt in (
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
        ):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                pass
        return None

    @staticmethod
    def _top_n_hours(hours: List[int], n: int = 3) -> List[int]:
        from collections import Counter
        counter = Counter(hours)
        return [h for h, _ in counter.most_common(n)]
