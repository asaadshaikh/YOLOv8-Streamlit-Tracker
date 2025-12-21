"""
Metrics collection for monitoring
Provides Prometheus-compatible metrics
"""
from typing import Dict
from datetime import datetime
from collections import defaultdict
import time

from utils.logger import logger


class MetricsCollector:
    """Collects application metrics"""
    
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = defaultdict(list)
        self.start_time = datetime.utcnow()
    
    def increment(self, metric_name: str, value: int = 1, labels: Dict = None):
        """Increment a counter metric"""
        key = self._make_key(metric_name, labels)
        self.counters[key] += value
    
    def set_gauge(self, metric_name: str, value: float, labels: Dict = None):
        """Set a gauge metric"""
        key = self._make_key(metric_name, labels)
        self.gauges[key] = value
    
    def record_histogram(self, metric_name: str, value: float, labels: Dict = None):
        """Record a histogram value"""
        key = self._make_key(metric_name, labels)
        self.histograms[key].append(value)
        # Keep only last 1000 values
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
    
    def record_timing(self, metric_name: str, start_time: float, labels: Dict = None):
        """Record timing metric"""
        duration = time.time() - start_time
        self.record_histogram(metric_name, duration, labels)
    
    def _make_key(self, metric_name: str, labels: Dict = None) -> str:
        """Create metric key with labels"""
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{metric_name}{{{label_str}}}"
        return metric_name
    
    def get_prometheus_format(self) -> str:
        """Get metrics in Prometheus format"""
        lines = []
        
        # Counters
        for key, value in self.counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self.gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")
        
        # Histograms (simplified - calculate mean)
        for key, values in self.histograms.items():
            if values:
                mean = sum(values) / len(values)
                lines.append(f"# TYPE {key.split('{')[0]} histogram")
                lines.append(f"{key}_mean {mean}")
                lines.append(f"{key}_count {len(values)}")
        
        # Uptime
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        lines.append(f"# TYPE visiontrack_uptime_seconds gauge")
        lines.append(f"visiontrack_uptime_seconds {uptime}")
        
        return "\n".join(lines)
    
    def get_summary(self) -> Dict:
        """Get metrics summary as dictionary"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histogram_stats": {
                key: {
                    "count": len(values),
                    "mean": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                }
                for key, values in self.histograms.items()
            },
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }


# Global metrics instance
metrics = MetricsCollector()

