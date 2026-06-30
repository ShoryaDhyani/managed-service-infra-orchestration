from dotenv import load_dotenv
from pydantic import BaseModel
import os
from typing import Optional
load_dotenv()


class Settings(BaseModel):
    PROJECT_ID: str = os.getenv("PROJECT_ID")
    REDIS_URL: str = os.getenv("REDIS_URL")

    SERVICE_TOKEN: str = os.getenv("SERVICE_TOKEN")

    S3_REGION: str = os.getenv("S3_REGION")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY")
    CLUSTER: str = os.getenv("CLUSTER")
    TASK: str = os.getenv("TASK")
    PROXY_BASE_PATH: str = os.getenv("PROXY_BASE_PATH", "localhost:8000")
    LOCAL: str = os.getenv("LOCAL", "false")

    PEPPER: str = os.getenv("PEPPER")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "900"))

    # postgres_user: str = os.getenv("POSTGRES_USER")
    # postgres_password: str = os.getenv("POSTGRES_PASSWORD")
    # postgres_host: str = os.getenv("POSTGRES_HOST")
    # postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_url: str = os.getenv("POSTGRES_URL")

    rabbitmq_url: str = os.getenv("RABBITMQ_URL")






config = Settings()