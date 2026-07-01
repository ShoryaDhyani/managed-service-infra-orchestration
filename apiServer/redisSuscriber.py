from logger import publish_log
import redis.asyncio as aioredis
from config import config


redis = aioredis.from_url(
    config.REDIS_URL,
    decode_responses=True,
    socket_keepalive=True,
    health_check_interval=30,
    retry_on_timeout=True,
)

async def init_redis_subscribe(manager):
    publish_log('Subscribed to logs....')
    pubsub = redis.pubsub()
    await pubsub.psubscribe('logs:*')
    try:
        async for message in pubsub.listen():
            if message['type'] == 'pmessage':
                channel = message['channel'].decode() if isinstance(message['channel'], bytes) else message['channel']
                data    = message['data'].decode()    if isinstance(message['data'],    bytes) else message['data']
                await manager.broadcast(channel, data)
    finally:
        await pubsub.close()