
import os
import json
import asyncio
from typing import Optional, Any

# Global cache storage for fallback
_MEMORY_CACHE = {}

class CacheManager:
    def __init__(self):
        self.redis = None
        self.use_redis = False
        
    async def initialize(self):
        # Check for REDIS_URL env var or default
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            import redis.asyncio as redis
            self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await self.redis.ping()
            self.use_redis = True
            print("✅ Connected to Redis Cache")
        except Exception as e:
            self.redis = None
            print(f"[Warning] Redis unavailable ({e}). Using In-Memory Cache.")
            self.use_redis = False

    async def get(self, key: str) -> Optional[Any]:
        if self.use_redis:
            try:
                val = await self.redis.get(key)
                return json.loads(val) if val else None
            except:
                return None
        return _MEMORY_CACHE.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300):
        if self.use_redis:
            try:
                await self.redis.setex(key, ttl, json.dumps(value))
            except:
                pass
        else:
            _MEMORY_CACHE[key] = value
            # Naive TTL implementation (cleanup is not implemented for simplicity in memory mode)

    async def delete(self, key: str):
        if self.use_redis:
            try:
                await self.redis.delete(key)
            except:
                pass
        else:
            _MEMORY_CACHE.pop(key, None)

    async def clear_pattern(self, pattern: str):
         # Pattern clearing is key for invalidation
         if self.use_redis:
             try:
                 keys = await self.redis.keys(pattern)
                 if keys:
                     await self.redis.delete(*keys)
             except:
                 pass
         else:
             # Memory pattern delete (prefix match)
             keys_to_del = [k for k in _MEMORY_CACHE.keys() if pattern.strip('*') in k]
             for k in keys_to_del:
                 del _MEMORY_CACHE[k]

cache = CacheManager()
