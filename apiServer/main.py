import asyncio
import uvicorn
import redis.asyncio as aioredis
from database.db import get_db
from projects.service import update_project_status
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from contextlib import asynccontextmanager
from config import config
from fastapi import Body
from logger import *
from rabbitmq import rabbitmq
from worker import main as wm
from database.init_db import create_tables
from routes.user import user_router
from routes.auth import auth_router
from sqlalchemy.orm import Session
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    task = asyncio.create_task(init_redis_subscribe())
    await rabbitmq.connect()
    worker= asyncio.create_task(wm())
    create_tables()
    redis = aioredis.from_url(
        config.REDIS_URL,
        decode_responses=True,
        socket_keepalive=True,
        health_check_interval=30,
    )
    await FastAPILimiter.init(redis)

    yield


    task.cancel()
    await rabbitmq.close()
    worker.cancel()
    await redis.close()

    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PORT = 9000
LOCAL=config.LOCAL.lower()
# Redis
subscriber = aioredis.from_url(
    config.REDIS_URL,
    decode_responses=True,
    socket_keepalive=True,
    health_check_interval=30,
)


app.include_router(user_router, prefix="/api/v1", tags=["User"], dependencies=[Depends(RateLimiter(times=10, seconds=60))])
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"], dependencies=[Depends(RateLimiter(times=5, seconds=60))])

# ── Connection Manager ────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        # { channel: [ws1, ws2, ...] }
        self.rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        self.rooms.setdefault(channel, []).append(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.rooms:
            self.rooms[channel].remove(websocket)
            if not self.rooms[channel]:
                del self.rooms[channel]

    async def broadcast(self, channel: str, message: str):
        for ws in self.rooms.get(channel, []):
            try:
                await ws.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()





@app.get('/health', dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def health_check():
    return {'status': 'ok'}


# ── WebSocket Endpoint ────────────────────────────────────────────
@app.websocket('/ws/{channel}')
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await manager.connect(websocket, channel)
    await websocket.send_text(f'Joined {channel}')
    try:
        while True:
            # Keep connection alive, listen for any client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
        publish_log(f'Client disconnected from {channel}')




@app.post('/buildstatus')
async def build_status(request: Request, body: dict = Body(...),db: Session = Depends(get_db)):
    # This is a placeholder. In a real implementation, you would check the build status from a database or cache.
    if request.headers.get("Authorization") != f"Bearer {config.SERVICE_TOKEN}":
        raise HTTPException(status_code=403, detail="Invalid service token")
    project_slug = body.get('slug')
    projectStatus = body.get('projectStatus')
    if projectStatus == 'failed':
        publish_error(f"Build failed for project: {project_slug}")
    update_project_status(db,project_slug,projectStatus)
    # Publish build status to Redis channel
    # await manager.broadcast(f'logs:{project_slug}', {"projectStatus": projectStatus})

# ── Redis Subscriber ──────────────────────────────────────────────
async def init_redis_subscribe():
    publish_log('Subscribed to logs....')
    pubsub = subscriber.pubsub()
    await pubsub.psubscribe('logs:*')
    async for message in pubsub.listen():
        if message['type'] == 'pmessage':
            channel = message['channel'].decode() if isinstance(message['channel'], bytes) else message['channel']
            data    = message['data'].decode()    if isinstance(message['data'],    bytes) else message['data']
            await manager.broadcast(channel, data)


# ── Startup ───────────────────────────────────────────────────────
if __name__ == '__main__':
    publish_log(f'API Server Running..{PORT}')
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=PORT,
        ws='websockets'
    )

