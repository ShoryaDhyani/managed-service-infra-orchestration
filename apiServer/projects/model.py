from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database.db import Base
import uuid
from typing import Optional

class Project(Base):
    __tablename__ = "projects"
    project_id = Column(String(255), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(255), unique=True, index=True, nullable=False)
    type = Column(String(255), nullable=False)
    gitURL = Column(String(255), nullable=False)
    user_id = Column(String(255),ForeignKey('users.id'), nullable=False)
    project_url = Column(String(255), nullable=True)
    status = Column(String(255), nullable=False, default="Unknown")

    user=relationship("User", back_populates="projects")

class ProjectRequest(BaseModel):
    gitURL: str
    slug: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = "pending"