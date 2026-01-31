"""
Health Check System for VyaparMind

Monitors system health including database connectivity, disk space,
memory usage, and external service availability.
"""

import os
import sqlite3
from typing import Dict, List, Tuple
from datetime import datetime
import config


class HealthCheck:
    """System health check utilities."""
    
    def __init__(self):
        self.checks = []
        self.status = "UNKNOWN"
    
    def check_database(self) -> Tuple[bool, str]:
        """Check database connectivity."""
        try:
            if config.DB_TYPE == "SQLITE":
                conn = sqlite3.connect(config.SQLITE_DB, timeout=5)
                conn.execute("SELECT 1")
                conn.close()
                return True, "Database connection OK"
            elif config.DB_TYPE == "POSTGRES":
                try:
                    import psycopg2
                    conn = psycopg2.connect(
                        host=config.PG_HOST,
                        port=config.PG_PORT,
                        database=config.PG_NAME,
                        user=config.PG_USER,
                        password=config.PG_PASS,
                        connect_timeout=5
                    )
                    conn.close()
                    return True, "Database connection OK"
                except Exception as e:
                    return False, f"Database connection failed: {str(e)}"
            else:
                return False, "Unknown database type"
        except Exception as e:
            return False, f"Database check failed: {str(e)}"
    
    def check_disk_space(self, threshold_percent: float = 90.0) -> Tuple[bool, str]:
        """Check disk space availability."""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            
            percent_used = (used / total) * 100
            free_gb = free / (1024**3)
            
            if percent_used > threshold_percent:
                return False, f"Disk space critical: {percent_used:.1f}% used, {free_gb:.2f}GB free"
            else:
                return True, f"Disk space OK: {percent_used:.1f}% used, {free_gb:.2f}GB free"
        except Exception as e:
            return False, f"Disk space check failed: {str(e)}"
    
    def check_memory(self, threshold_percent: float = 90.0) -> Tuple[bool, str]:
        """Check memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            if memory.percent > threshold_percent:
                return False, f"Memory usage critical: {memory.percent:.1f}% used"
            else:
                return True, f"Memory usage OK: {memory.percent:.1f}% used"
        except ImportError:
            return True, "Memory check skipped (psutil not installed)"
        except Exception as e:
            return False, f"Memory check failed: {str(e)}"
    
    def check_database_size(self, max_size_mb: float = 1000.0) -> Tuple[bool, str]:
        """Check database file size."""
        try:
            if config.DB_TYPE == "SQLITE":
                if os.path.exists(config.SQLITE_DB):
                    size_mb = os.path.getsize(config.SQLITE_DB) / (1024**2)
                    if size_mb > max_size_mb:
                        return False, f"Database size large: {size_mb:.2f}MB (threshold: {max_size_mb}MB)"
                    else:
                        return True, f"Database size OK: {size_mb:.2f}MB"
                else:
                    return False, "Database file not found"
            else:
                return True, "Database size check skipped (PostgreSQL)"
        except Exception as e:
            return False, f"Database size check failed: {str(e)}"
    
    def check_log_directory(self) -> Tuple[bool, str]:
        """Check if log directory exists and is writable."""
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                return True, "Log directory created"
            
            # Test write permission
            test_file = os.path.join(log_dir, ".health_check_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            return True, "Log directory OK"
        except Exception as e:
            return False, f"Log directory check failed: {str(e)}"
    
    def check_external_services(self) -> Tuple[bool, str]:
        """Check external service connectivity (placeholder)."""
        # This would check email, WhatsApp, payment gateways, etc.
        # For now, just return OK
        return True, "External services check skipped"
    
    def run_all_checks(self) -> Dict:
        """Run all health checks."""
        checks = {
            'database': self.check_database(),
            'disk_space': self.check_disk_space(),
            'memory': self.check_memory(),
            'database_size': self.check_database_size(),
            'log_directory': self.check_log_directory(),
            'external_services': self.check_external_services(),
        }
        
        # Determine overall status
        all_passed = all(check[0] for check in checks.values())
        critical_failed = not checks['database'][0]
        
        if critical_failed:
            self.status = "CRITICAL"
        elif not all_passed:
            self.status = "WARNING"
        else:
            self.status = "HEALTHY"
        
        return {
            'status': self.status,
            'timestamp': datetime.now().isoformat(),
            'checks': {
                name: {
                    'passed': result[0],
                    'message': result[1]
                }
                for name, result in checks.items()
            }
        }
    
    def get_health_report(self) -> str:
        """Generate a health report."""
        results = self.run_all_checks()
        
        report = []
        report.append("="*60)
        report.append("SYSTEM HEALTH REPORT")
        report.append("="*60)
        report.append(f"Status: {results['status']}")
        report.append(f"Timestamp: {results['timestamp']}")
        report.append("")
        
        for check_name, check_result in results['checks'].items():
            status_icon = "✅" if check_result['passed'] else "❌"
            report.append(f"{status_icon} {check_name.replace('_', ' ').title()}")
            report.append(f"   {check_result['message']}")
        
        report.append("="*60)
        
        return "\n".join(report)


# Global health check instance
health_checker = HealthCheck()


def get_system_health() -> Dict:
    """Get current system health status."""
    return health_checker.run_all_checks()


def is_system_healthy() -> bool:
    """Check if system is healthy."""
    results = health_checker.run_all_checks()
    return results['status'] in ['HEALTHY', 'WARNING']


# Example usage
if __name__ == "__main__":
    print(health_checker.get_health_report())
