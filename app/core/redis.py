from redis.asyncio import Redis

from app.core import config

redis_client: Redis = Redis.from_url(config.REDIS_URL, decode_responses=True)
