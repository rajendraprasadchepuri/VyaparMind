"""
Performance Monitoring and Metrics for VyaparMind

Tracks query execution times, memory usage, and application performance metrics.
"""

import time
import functools
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime
import json
import os


class PerformanceMonitor:
    """Monitor and track application performance."""
    
    def __init__(self):
        self.metrics = []
        self.slow_queries = []
        self.threshold_ms = 100  # Slow query threshold
    
    def record_metric(self, operation: str, duration_ms: float, 
                     context: Optional[Dict] = None):
        """Record a performance metric."""
        metric = {
            'operation': operation,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        self.metrics.append(metric)
        
        # Track slow queries
        if duration_ms > self.threshold_ms:
            self.slow_queries.append(metric)
    
    def get_stats(self) -> Dict:
        """Get performance statistics."""
        if not self.metrics:
            return {
                'total_operations': 0,
                'avg_duration_ms': 0,
                'max_duration_ms': 0,
                'min_duration_ms': 0,
                'slow_queries_count': 0
            }
        
        durations = [m['duration_ms'] for m in self.metrics]
        return {
            'total_operations': len(self.metrics),
            'avg_duration_ms': sum(durations) / len(durations),
            'max_duration_ms': max(durations),
            'min_duration_ms': min(durations),
            'slow_queries_count': len(self.slow_queries),
            'slow_queries': self.slow_queries[-10:]  # Last 10 slow queries
        }
    
    def reset(self):
        """Reset all metrics."""
        self.metrics = []
        self.slow_queries = []
    
    def export_metrics(self, filepath: str = 'performance_metrics.json'):
        """Export metrics to JSON file."""
        with open(filepath, 'w') as f:
            json.dump({
                'stats': self.get_stats(),
                'all_metrics': self.metrics
            }, f, indent=2)


# Global monitor instance
monitor = PerformanceMonitor()


def track_performance(operation_name: Optional[str] = None):
    """
    Decorator to track function performance.
    
    Usage:
        @track_performance("fetch_products")
        def fetch_products():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            op_name = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                monitor.record_metric(op_name, duration_ms)
        
        return wrapper
    return decorator


def measure_time(operation: str, context: Optional[Dict] = None):
    """
    Context manager to measure execution time.
    
    Usage:
        with measure_time("database_query", {"query": "SELECT..."}):
            # code to measure
            pass
    """
    class TimeMeasurement:
        def __init__(self, op: str, ctx: Optional[Dict]):
            self.operation = op
            self.context = ctx
            self.start_time = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            duration_ms = (time.time() - self.start_time) * 1000
            monitor.record_metric(self.operation, duration_ms, self.context)
    
    return TimeMeasurement(operation, context)


# Database-specific performance tracking
class QueryPerformanceTracker:
    """Track database query performance."""
    
    def __init__(self):
        self.query_stats = {}
    
    def track_query(self, query_type: str, duration_ms: float, 
                   rows_affected: int = 0):
        """Track a database query."""
        if query_type not in self.query_stats:
            self.query_stats[query_type] = {
                'count': 0,
                'total_duration_ms': 0,
                'avg_duration_ms': 0,
                'max_duration_ms': 0,
                'total_rows': 0
            }
        
        stats = self.query_stats[query_type]
        stats['count'] += 1
        stats['total_duration_ms'] += duration_ms
        stats['avg_duration_ms'] = stats['total_duration_ms'] / stats['count']
        stats['max_duration_ms'] = max(stats['max_duration_ms'], duration_ms)
        stats['total_rows'] += rows_affected
    
    def get_query_stats(self) -> Dict:
        """Get query statistics."""
        return self.query_stats
    
    def get_slowest_queries(self, limit: int = 10) -> List[tuple]:
        """Get slowest query types."""
        sorted_queries = sorted(
            self.query_stats.items(),
            key=lambda x: x[1]['avg_duration_ms'],
            reverse=True
        )
        return sorted_queries[:limit]


# Global query tracker
query_tracker = QueryPerformanceTracker()


# Memory usage tracking
def get_memory_usage() -> Dict:
    """Get current memory usage (requires psutil)."""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent()
        }
    except ImportError:
        return {'error': 'psutil not installed'}


# Performance report generation
def generate_performance_report() -> str:
    """Generate a performance report."""
    stats = monitor.get_stats()
    query_stats = query_tracker.get_query_stats()
    memory = get_memory_usage()
    
    report = []
    report.append("="*60)
    report.append("PERFORMANCE REPORT")
    report.append("="*60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    report.append("GENERAL METRICS:")
    report.append(f"  Total Operations: {stats['total_operations']}")
    report.append(f"  Average Duration: {stats['avg_duration_ms']:.2f}ms")
    report.append(f"  Max Duration: {stats['max_duration_ms']:.2f}ms")
    report.append(f"  Min Duration: {stats['min_duration_ms']:.2f}ms")
    report.append(f"  Slow Queries: {stats['slow_queries_count']}")
    report.append("")
    
    if query_stats:
        report.append("DATABASE QUERY STATS:")
        for query_type, qstats in query_stats.items():
            report.append(f"  {query_type}:")
            report.append(f"    Count: {qstats['count']}")
            report.append(f"    Avg Duration: {qstats['avg_duration_ms']:.2f}ms")
            report.append(f"    Max Duration: {qstats['max_duration_ms']:.2f}ms")
            report.append(f"    Total Rows: {qstats['total_rows']}")
        report.append("")
    
    if 'error' not in memory:
        report.append("MEMORY USAGE:")
        report.append(f"  RSS: {memory['rss_mb']:.2f} MB")
        report.append(f"  VMS: {memory['vms_mb']:.2f} MB")
        report.append(f"  Percent: {memory['percent']:.2f}%")
        report.append("")
    
    if stats['slow_queries_count'] > 0:
        report.append("RECENT SLOW QUERIES:")
        for sq in stats['slow_queries'][-5:]:
            report.append(f"  {sq['operation']}: {sq['duration_ms']:.2f}ms")
            if sq['context']:
                report.append(f"    Context: {sq['context']}")
        report.append("")
    
    report.append("="*60)
    
    return "\n".join(report)


# Example usage
if __name__ == "__main__":
    # Test performance tracking
    @track_performance("test_operation")
    def test_function():
        time.sleep(0.05)  # Simulate work
        return "done"
    
    # Run test operations
    for i in range(10):
        test_function()
    
    # Track some queries
    query_tracker.track_query("SELECT", 45.5, 100)
    query_tracker.track_query("INSERT", 12.3, 1)
    query_tracker.track_query("SELECT", 150.2, 500)  # Slow query
    
    # Generate report
    print(generate_performance_report())
    
    # Export metrics
    monitor.export_metrics()
    print("\nMetrics exported to performance_metrics.json")
