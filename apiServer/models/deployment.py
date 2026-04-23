from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from db.base import Base


class DeploymentStatus(str, enum.Enum):
    QUEUED = "queued"
    BUILDING = "building"
    SUCCESS = "success"
    FAILED = "failed"


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)

    commit_hash = Column(String, nullable=True)
    branch = Column(String, nullable=True)

    status = Column(Enum(DeploymentStatus), default=DeploymentStatus.QUEUED)

    build_logs = Column(String, nullable=True)
    deployed_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # relations
    project = relationship("Project", back_populates="deployments")