import redis.asyncio as redis

redis_client = redis.Redis(
    host="10.1.115.170",
    port=6379,
    db=0,
    decode_responses=True
)
