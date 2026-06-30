from database.db import Base
from sqlalchemy import CheckConstraint, Column, Integer, String
from sqlalchemy.orm import relationship
import uuid
from pydantic import BaseModel
from fastapi import Request
class User(Base):
    __tablename__ = "users"
    id = Column(String(255), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    no_of_projects = Column(Integer(), nullable=True,default=0)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "no_of_projects BETWEEN 0 AND 5",
            name="ck_no_of_projects_range",
        ),
    )

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserToken(BaseModel):
    access_token: str
    token_type: str = "bearer"