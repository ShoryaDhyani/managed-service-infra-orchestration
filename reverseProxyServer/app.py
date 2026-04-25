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

# Root domain names that should go to webapp (localhost:9000)
ROOT_DOMAINS = {'msio', 'www', ''}


def get_target_url(request: Request, path: str) -> str:
    hostname = request.headers.get('host', '').split(':')[0]
    # e.g. aaa.msio.shoryadhyani.me  →  subdomain = 'aaa'
    #      msio.shoryadhyani.me       →  subdomain = 'msio'
    subdomain = hostname.split('.')[0]

    if subdomain in ROOT_DOMAINS:
        # Root domain → forward to webapp container
        target = f'http://localhost:9000'
        return f'{target}/{path}' if path else target
    else:
        # Wildcard subdomain → proxy to S3
        return f'{BASE_PATH}/{subdomain}/{path}' if path else f'{BASE_PATH}/{subdomain}/index.html'


@app.api_route(
    '/{path:path}',
    methods=['GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']
)
async def reverse_proxy(request: Request, path: str):
    target_url = get_target_url(request, path)

    # Debug log — remove after confirming it works
    print(f'[proxy] host={request.headers.get("host")} → {target_url}')

    headers = dict(request.headers)
    headers.pop('host', None)

    body = await request.body()

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=dict(request.query_params),
                follow_redirects=False
            )
        except httpx.RequestError as e:
            print(f'[proxy] error: {e}')
            return HTMLResponse(
                content=f'<h1>502 Bad Gateway</h1><p>{str(e)}</p>',
                status_code=502
            )

    if resp.status_code in (403, 404):
        return HTMLResponse(content=NOT_FOUND_HTML, status_code=404)

    excluded_headers = {'content-encoding', 'transfer-encoding', 'connection'}
    response_headers = {
        k: v for k, v in resp.headers.items()
        if k.lower() not in excluded_headers
    }

    return StreamingResponse(
        content=iter([resp.content]),
        status_code=resp.status_code,
        headers=response_headers
    )


if __name__ == '__main__':
    print('Reverse Proxy running on port 8000...')
    uvicorn.run(app, host='0.0.0.0', port=8000)