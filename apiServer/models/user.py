from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    github_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    access_token = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # relations
    projects = relationship("Project", back_populates="owner", cascade="all, delete")