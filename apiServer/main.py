import asyncio
from fastapi.staticfiles import StaticFiles
from httpcore import request
import uvicorn
import redis.asyncio as aioredis
import boto3
from coolname import generate_slug
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import Request
from contextlib import asynccontextmanager
from config import config
from config import ProjectRequest



@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(init_redis_subscribe())
    
    yield
    
    task.cancel()
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


def run_build_container(body: ProjectRequest, project_slug: str, request: Request):
    try:
        ecs_client.run_task(
            cluster=container_config['CLUSTER'],
            taskDefinition=container_config['TASK'],
            launchType='FARGATE',
            count=1,
            networkConfiguration={
                'awsvpcConfiguration': {
                    'assignPublicIp': 'ENABLED',
                    'subnets': ['subnet-0d9261d1bac8665af', 'subnet-03eb8bca8687f02d8', 'subnet-0afe74c57cdd4e235'],
                    'securityGroups': ['sg-0d8483897cb94cd43']
                }
            },
            overrides={
                'containerOverrides': [
                    {
                        'name': 'builder-image',
                        'environment': [
                            {'name': 'GIT_URL', 'value': body.gitURL},
                            {'name': 'PROJECT_ID', 'value': project_slug},
                            {'name': 'PROJECT_TYPE', 'value': body.type}
                        ]
                    }
                ]
            }
        )

        # Get protocol + host from request
        host = request.headers.get("host")
        proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    
    except Exception as e:
        print(f'Error running ECS task: {e}')
        return None, None

    return host, proto



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



@app.get('/health')
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
        print(f'Client disconnected from {channel}')


# ── Request Model ─────────────────────────────────────────────────
app.mount('/assets', StaticFiles(directory='static/assets'), name='assets')
@app.get('/')
async def root(request: Request):
    return FileResponse('static/index.html')

# ── Routes ────────────────────────────────────────────────────────
@app.post('/project')
async def create_project(body: ProjectRequest, request: Request):
    project_slug = body.slug if body.slug else generate_slug(2)

    if body.type not in ['react', 'static']:
        return {
            'status': 'error',
            'message': 'Invalid project type. Must be either "react" or "static".'
        }
    

    host,proto=run_build_container(body, project_slug, request)


    if not host or not proto:
        return {
            'status': 'error',
            'message': 'Invalid host or protocol.'
        }

    return {
        'status': 'queued',
        'data': {
            'projectSlug': project_slug,
            'url': f'{proto}://{project_slug}.{host}'
        }
    }




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