import httpx
from urllib.parse import urlencode
from config import config


class GitHubService:

    BASE_URL = "https://github.com/login/oauth"
    API_URL = "https://api.github.com"

    @staticmethod
    def get_authorization_url():
        params = {
            "client_id": config.GITHUB_CLIENT_ID,
            "scope": "repo user",
        }
        return f"{GitHubService.BASE_URL}/authorize?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_token(code: str):
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{GitHubService.BASE_URL}/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": config.GITHUB_CLIENT_ID,
                    "client_secret": config.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
            )

        data = res.json()

        if "access_token" not in data:
            raise Exception("Failed to get access token")

        return data["access_token"]

    @staticmethod
    async def get_user(token: str):
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{GitHubService.API_URL}/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )

        return res.json()