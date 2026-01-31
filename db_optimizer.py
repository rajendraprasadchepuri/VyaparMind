"""
Database Optimization Utilities for VyaparMind

Provides tools for query optimization, index management, and performance tuning.
"""

import sqlite3
import config
from typing import List, Dict, Tuple
from logger import log_info, log_warning, log_error


class DatabaseOptimizer:
    """Database optimization utilities."""
    
    def __init__(self):
        self.recommendations = []
    
    def analyze_table_indexes(self, conn) -> List[Dict]:
        """Analyze existing indexes."""
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        index_info = []
        for table in tables:
            cursor.execute(f"PRAGMA index_list('{table}')")
            indexes = cursor.fetchall()
            
            for idx in indexes:
                cursor.execute(f"PRAGMA index_info('{idx[1]}')")
                columns = [col[2] for col in cursor.fetchall()]
                
                index_info.append({
                    'table': table,
                    'index_name': idx[1],
                    'unique': bool(idx[2]),
                    'columns': columns
                })
        
        return index_info
    
    def recommend_indexes(self, conn) -> List[str]:
        """Recommend indexes based on table structure."""
        recommendations = []
        cursor = conn.cursor()
        
        # Common patterns that benefit from indexes
        index_patterns = [
            ('products', 'account_id'),
            ('products', 'category'),
            ('transactions', 'account_id'),
            ('transactions', 'timestamp'),
            ('customers', 'account_id'),
            ('customers', 'phone'),
            ('batches', 'account_id'),
            ('batches', 'expiry_date'),
            ('suppliers', 'account_id'),
            ('purchase_orders', 'account_id'),
            ('purchase_orders', 'status'),
            ('users', 'account_id'),
            ('users', 'username'),
        ]
        
        existing_indexes = self.analyze_table_indexes(conn)
        existing_set = {(idx['table'], tuple(idx['columns'])) for idx in existing_indexes}
        
        for table, column in index_patterns:
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                continue
            
            # Check if column exists
            cursor.execute(f"PRAGMA table_info('{table}')")
            columns = [col[1] for col in cursor.fetchall()]
            if column not in columns:
                continue
            
            # Check if index already exists
            if (table, (column,)) not in existing_set:
                index_name = f"idx_{table}_{column}"
                recommendations.append(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column});")
        
        return recommendations
    
    def create_recommended_indexes(self, conn) -> Tuple[int, List[str]]:
        """Create recommended indexes."""
        recommendations = self.recommend_indexes(conn)
        created = []
        
        for sql in recommendations:
            try:
                conn.execute(sql)
                created.append(sql)
                log_info(f"Created index: {sql}")
            except Exception as e:
                log_warning(f"Failed to create index: {sql} - {e}")
        
        conn.commit()
        return len(created), created
    
    def analyze_query_plan(self, conn, query: str) -> str:
        """Analyze query execution plan."""
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN QUERY PLAN {query}")
        plan = cursor.fetchall()
        
        plan_text = []
        for row in plan:
            plan_text.append(" | ".join(str(x) for x in row))
        
        return "\n".join(plan_text)
    
    def vacuum_database(self, conn):
        """Vacuum database to reclaim space and optimize."""
        try:
            conn.execute("VACUUM")
            log_info("Database vacuumed successfully")
        except Exception as e:
            log_error(f"Failed to vacuum database: {e}")
    
    def analyze_database(self, conn):
        """Analyze database statistics."""
        try:
            conn.execute("ANALYZE")
            log_info("Database analyzed successfully")
        except Exception as e:
            log_error(f"Failed to analyze database: {e}")
    
    def get_table_stats(self, conn) -> List[Dict]:
        """Get statistics for all tables."""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        stats = []
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            
            stats.append({
                'table': table,
                'row_count': row_count
            })
        
        return stats
    
    def optimize_database(self, conn) -> Dict:
        """Run full database optimization."""
        log_info("Starting database optimization...")
        
        results = {
            'indexes_created': 0,
            'indexes_sql': [],
            'table_stats': [],
            'vacuumed': False,
            'analyzed': False
        }
        
        # Create recommended indexes
        count, sqls = self.create_recommended_indexes(conn)
        results['indexes_created'] = count
        results['indexes_sql'] = sqls
        
        # Get table statistics
        results['table_stats'] = self.get_table_stats(conn)
        
        # Vacuum database
        try:
            self.vacuum_database(conn)
            results['vacuumed'] = True
        except:
            pass
        
        # Analyze database
        try:
            self.analyze_database(conn)
            results['analyzed'] = True
        except:
            pass
        
        log_info(f"Database optimization complete: {count} indexes created")
        
        return results


# Caching utilities
class CacheManager:
    """Manage application caching."""
    
    def __init__(self):
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get(self, key: str):
        """Get value from cache."""
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        else:
            self.cache_misses += 1
            return None
    
    def set(self, key: str, value, ttl: int = 300):
        """Set value in cache with TTL (seconds)."""
        self.cache[key] = value
    
    def clear(self, pattern: str = None):
        """Clear cache entries matching pattern."""
        if pattern is None:
            self.cache = {}
        else:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': hit_rate
        }


# Global instances
optimizer = DatabaseOptimizer()
cache_manager = CacheManager()


# Convenience functions
def optimize_database():
    """Optimize the current database."""
    if config.DB_TYPE == "SQLITE":
        conn = sqlite3.connect(config.SQLITE_DB)
        results = optimizer.optimize_database(conn)
        conn.close()
        return results
    else:
        return {'error': 'Optimization only supported for SQLite'}


def get_query_plan(query: str) -> str:
    """Get execution plan for a query."""
    if config.DB_TYPE == "SQLITE":
        conn = sqlite3.connect(config.SQLITE_DB)
        plan = optimizer.analyze_query_plan(conn, query)
        conn.close()
        return plan
    else:
        return "Query plan analysis only supported for SQLite"


# Example usage
if __name__ == "__main__":
    print("Running database optimization...")
    results = optimize_database()
    
    print(f"\n✅ Optimization Complete:")
    print(f"  - Indexes created: {results['indexes_created']}")
    print(f"  - Database vacuumed: {results['vacuumed']}")
    print(f"  - Database analyzed: {results['analyzed']}")
    
    print(f"\n📊 Table Statistics:")
    for stat in results['table_stats']:
        print(f"  - {stat['table']}: {stat['row_count']} rows")
    
    if results['indexes_sql']:
        print(f"\n🔧 Indexes Created:")
        for sql in results['indexes_sql']:
            print(f"  - {sql}")
