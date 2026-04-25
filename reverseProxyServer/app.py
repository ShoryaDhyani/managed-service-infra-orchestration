from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
import httpx
import uvicorn

app = FastAPI()

BASE_PATH = 'https://msio-outputs.s3.ap-south-1.amazonaws.com/__outputs'

NOT_FOUND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 - Page Not Found</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f0f;
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .container { text-align: center; padding: 2rem; }
        h1 { font-size: 8rem; font-weight: 800; color: #333; line-height: 1; }
        h2 { font-size: 1.5rem; font-weight: 400; color: #aaa; margin-top: 0.5rem; }
        p  { color: #666; margin-top: 1rem; font-size: 0.95rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>404</h1>
        <h2>Page Not Found</h2>
        <p>The page you're looking for doesn't exist or is unavailable.</p>
    </div>
</body>
</html>
"""





def get_target_url(request: Request, path: str) -> str:
    hostname = request.headers.get('host', '').split(':')[0]
    subdomain = hostname.split('.')[0]
    resolved = f'{BASE_PATH}/{subdomain}'
    return f'{resolved}/{path}' if path else f'{resolved}/index.html'

@app.get('/')
async def root(request: Request):
    return {'status': "ok"}

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

    # Show 404 page for missing files or S3 access denied responses
    if resp.status_code in (403, 404):
        return HTMLResponse(content=NOT_FOUND_HTML, status_code=404)

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
    print(f'Reverse Proxy Running..8000')
    uvicorn.run(app, host='0.0.0.0', port=8000)
