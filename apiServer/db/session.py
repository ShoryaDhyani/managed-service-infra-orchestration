from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import config

engine = create_engine(config.DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

