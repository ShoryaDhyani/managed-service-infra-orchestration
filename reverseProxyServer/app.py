from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx
import uvicorn

app = FastAPI()

PORT = 8000
BASE_PATH = 'https://msio-outputs.s3.ap-south-1.amazonaws.com/__outputs'


def get_target_url(request: Request, path: str) -> str:
    hostname = request.headers.get('host', '').split(':')[0]
    subdomain = hostname.split('.')[0]
    resolved = f'{BASE_PATH}/{subdomain}'
    return f'{resolved}/{path}' if path else f'{resolved}/index.html'


@app.api_route('/{path:path}', methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])
async def reverse_proxy(request: Request, path: str):
    target_url = get_target_url(request, path)

    headers = dict(request.headers)
    headers.pop('host', None)

    body = await request.body()

    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=dict(request.query_params),
            follow_redirects=False
        )

    excluded_headers = {'content-encoding', 'transfer-encoding', 'connection'}
    response_headers = {
        key: val for key, val in resp.headers.items()
        if key.lower() not in excluded_headers
    }

    return StreamingResponse(
        content=iter([resp.content]),
        status_code=resp.status_code,
        headers=response_headers
    )


if __name__ == '__main__':
    print(f'Reverse Proxy Running..{PORT}')
    uvicorn.run(app, host='0.0.0.0', port=PORT)