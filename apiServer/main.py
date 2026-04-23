import asyncio
import json
from fastapi.staticfiles import StaticFiles
import uvicorn
import redis.asyncio as aioredis
import boto3
from coolname import generate_slug
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from typing import Optional
from fastapi import Request
from contextlib import asynccontextmanager
from config import config
from config import ProjectRequest
import httpx
from sqlalchemy.orm import Session

from db.deps import get_db
from db.base import Base
from services.github_service import GitHubService
from services.auth_service import AuthService
from db.session import engine
from models import User

def init_db():
    Base.metadata.create_all(bind=engine)


def get_current_user(db: Session = Depends(get_db)):
    # TEMP: replace with JWT later
    user = db.query(User).first()

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return user



@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(init_redis_subscribe())
    init_db()
    
    yield
    
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PORT = 9000

# Redis
subscriber = aioredis.from_url(config.REDIS_URL)

# ECS
ecs_client = boto3.client(
    'ecs',
    region_name='ap-south-1',
    aws_access_key_id=config.S3_ACCESS_KEY,
    aws_secret_access_key=config.S3_SECRET_KEY
)

container_config = {
    'CLUSTER': config.CLUSTER,
    'TASK': config.TASK
}


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
        print(f'Client disconnected from {channel}')


# ── Request Model ─────────────────────────────────────────────────
app.mount('/static', StaticFiles(directory='static'), name='static')
@app.get('/')
async def root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

# ── Routes ────────────────────────────────────────────────────────
@app.post('/project')
async def create_project(body: ProjectRequest):
    project_slug = body.slug if body.slug else generate_slug(2)

    ecs_client.run_task(
        cluster=container_config['CLUSTER'],
        taskDefinition=container_config['TASK'],
        launchType='FARGATE',
        count=1,
        networkConfiguration={
            'awsvpcConfiguration': {
                'assignPublicIp': 'ENABLED',
                'subnets': ['subnet-0520791c3baa38982', 'subnet-0c36cc1c2f8b9e66d', 'subnet-03c815f83e773e859'],
                'securityGroups': ['sg-0a53d64eee423e1ac']
            }
        },
        overrides={
            'containerOverrides': [
                {
                    'name': 'builder-image',
                    'environment': [
                        {'name': 'GIT_URL', 'value': body.gitURL},
                        {'name': 'PROJECT_ID',          'value': project_slug}
                    ]
                }
            ]
        }
    )

    return {
        'status': 'queued',
        'data': {
            'projectSlug': project_slug,
            'url': f'http://{project_slug}.localhost:8000'
        }
    }


@app.get('/auth/github/login')
async def github_login():
    url = GitHubService.get_authorization_url()
    return {"auth_url": url}


@app.get("/auth/github/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    try:
        token = await GitHubService.exchange_code_for_token(code)
        github_user = await GitHubService.get_user(token)

        user = AuthService.upsert_github_user(db, github_user, token)

        # return JWT or session
        return {
            "access_token": token,
            "user": {
                "id": user.id,
                "username": user.username
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── Redis Subscriber ──────────────────────────────────────────────
async def init_redis_subscribe():
    print('Subscribed to logs....')
    pubsub = subscriber.pubsub()
    await pubsub.psubscribe('logs:*')
    async for message in pubsub.listen():
        if message['type'] == 'pmessage':
            channel = message['channel'].decode() if isinstance(message['channel'], bytes) else message['channel']
            data    = message['data'].decode()    if isinstance(message['data'],    bytes) else message['data']
            await manager.broadcast(channel, data)


# ── Startup ───────────────────────────────────────────────────────




if __name__ == '__main__':
    print(f'API Server Running..{PORT}')
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=PORT,
        ws='websockets'
    )