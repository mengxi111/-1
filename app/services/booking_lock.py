import logging
import secrets
from contextlib import contextmanager

from redis import Redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


class RedisLockBusyError(Exception):
    pass


class RedisUnavailableError(Exception):
    pass


RELEASE_LOCK_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
"""


def build_booking_lock_key(store_id: int, seat_id: int) -> str:
    # Lock at seat granularity instead of exact time-window granularity.
    # This guarantees that all booking attempts for the same seat are serialized,
    # and the database overlap check becomes the final source of truth.
    return f"seat:{store_id}:{seat_id}"


@contextmanager
def redis_booking_lock(redis_client: Redis, key: str, ttl_ms: int):
    token = secrets.token_hex(16)
    try:
        acquired = redis_client.set(key, token, nx=True, px=ttl_ms)
    except RedisError as exc:
        logger.exception("预约锁 Redis 调用失败: key=%s ttl_ms=%s error=%s", key, ttl_ms, exc)
        raise RedisUnavailableError("redis unavailable") from exc

    if not acquired:
        raise RedisLockBusyError("booking lock busy")

    try:
        yield
    finally:
        try:
            redis_client.eval(RELEASE_LOCK_SCRIPT, 1, key, token)
        except RedisError:
            # Expired lock or temporary redis issue should not block request completion.
            pass
