from functools import lru_cache

from redis import Redis

from app.core.config import settings


def create_redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


@lru_cache(maxsize=1)
def get_cached_redis_client() -> Redis:
    return create_redis_client()


redis_client = get_cached_redis_client()
