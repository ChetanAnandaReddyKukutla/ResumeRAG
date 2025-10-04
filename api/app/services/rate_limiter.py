import time
from typing import Optional
import redis.asyncio as aioredis
import os


class RateLimiter:
    """Token bucket rate limiter using Redis"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = None
        self.capacity = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
        self.window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
        self.disabled = os.getenv("TEST_DISABLE_RATE_LIMIT") == "1"
    
    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: User identifier (user_id or IP address)
        
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        # Re-evaluate disabled flag each call so env changes during tests are honored
        if self.disabled or os.getenv("TEST_DISABLE_RATE_LIMIT") == "1":
            return True
        await self.connect()
        if self.redis_client is None:  # Safety guard
            return True

        key = f"rate_limit:{user_id}"
        current_time = int(time.time())
        window_start = current_time - self.window

        # Use Redis sorted set for sliding window
        pipe = self.redis_client.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(current_time): current_time})

        # Set expiry on key
        pipe.expire(key, self.window)

        results = await pipe.execute()

        # results[1] contains the count before adding current request
        request_count = results[1]

        # Check if limit exceeded
        if request_count >= self.capacity:
            return False

        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(user_id: str) -> bool:
    """
    Check rate limit for user
    
    Args:
        user_id: User identifier
    
    Returns:
        True if allowed, False if rate limit exceeded
    """
    return await rate_limiter.check_rate_limit(user_id)
