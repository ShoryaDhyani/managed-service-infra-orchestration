from dotenv import load_dotenv
from pydantic import BaseModel
import os
from typing import Optional
load_dotenv()


class Settings(BaseModel):
    PROJECT_ID: str = os.getenv("PROJECT_ID")
    REDIS_URL: str = os.getenv("REDIS_URL")
    S3_REGION: str = os.getenv("S3_REGION")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY")
    CLUSTER: str = os.getenv("CLUSTER")
    TASK: str = os.getenv("TASK")
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

class ProjectRequest(BaseModel):
    gitURL: str
    slug: Optional[str] = None


config = Settings()