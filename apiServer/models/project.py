from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    branch = Column(String, default="main")

    framework = Column(String, nullable=True)  # nextjs, vite, etc.
    build_command = Column(String, default="npm run build")
    output_dir = Column(String, default="dist")

    created_at = Column(DateTime, default=datetime.utcnow)

    # foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # relations
    owner = relationship("User", back_populates="projects")
    deployments = relationship(
        "Deployment",
        back_populates="project",
        cascade="all, delete"
    )