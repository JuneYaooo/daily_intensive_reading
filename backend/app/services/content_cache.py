import hashlib
import os

import redis
from dotenv import load_dotenv

from ..utils.logger import BeijingLogger


logger = BeijingLogger().get_logger()

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Content cache TTL (14 days)
CONTENT_CACHE_TTL = 14 * 24 * 60 * 60


def create_redis_client():
    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
        client.ping()
        logger.info("Redis connection established successfully")
        return client
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return None


redis_client = create_redis_client()


def get_url_cache_key(url: str) -> str:
    """Generate cache key for URL content."""
    return f"content:{hashlib.md5(url.encode()).hexdigest()}"


def cache_content(url: str, content: str) -> None:
    """Cache scraped content in Redis."""
    if not redis_client:
        return

    try:
        cache_key = get_url_cache_key(url)
        redis_client.setex(cache_key, CONTENT_CACHE_TTL, content)
        logger.info(f"Cached content for URL: {url[:100]}...")
    except Exception as e:
        logger.warning(f"Failed to cache content: {e}")


def get_cached_content(url: str) -> str | None:
    """Get cached content from Redis."""
    if not redis_client:
        return None

    try:
        cache_key = get_url_cache_key(url)
        content = redis_client.get(cache_key)
        if content:
            logger.info(f"Retrieved cached content for URL: {url[:100]}...")
            return content
        return None
    except Exception as e:
        logger.warning(f"Failed to get cached content: {e}")
        return None


def delete_cached_content(url: str) -> None:
    """Delete cached content for a URL."""
    if not redis_client:
        return

    try:
        redis_client.delete(get_url_cache_key(url))
    except Exception:
        pass
