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
from wsManager import manager
from redisSuscriber import init_redis_subscribe, redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    await FastAPILimiter.init(redis)
    task = asyncio.create_task(init_redis_subscribe(manager=manager))
    await rabbitmq.connect()
    worker= asyncio.create_task(wm())
    create_tables()
    

    yield


    task.cancel()
    worker.cancel()
    await rabbitmq.close()
    await redis.close()

    try:
        await worker
    except asyncio.CancelledError:
        pass
    
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



app.include_router(user_router, prefix="/api/v1", tags=["User"], dependencies=[Depends(RateLimiter(times=10, seconds=60))])
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"], dependencies=[Depends(RateLimiter(times=5, seconds=60))])



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




@app.post('/buildstatus', dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def build_status(request: Request, body: dict = Body(...),db: Session = Depends(get_db)):
    # This is a placeholder. In a real implementation, you would check the build status from a database or cache.
    if request.headers.get("Authorization") != f"Bearer {config.SERVICE_TOKEN}":
        raise HTTPException(status_code=403, detail="Invalid service token")
    project_slug = body.get('slug')
    projectStatus = body.get('projectStatus')
    if projectStatus == 'failed':
        publish_error(f"Build failed for project: {project_slug}")
    update_project_status(project_slug=project_slug,new_status=projectStatus,db=db)




PORT=9000
if __name__ == '__main__':
    publish_log(f'API Server Running..{PORT}')
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=PORT,
        ws='websockets'
    )

