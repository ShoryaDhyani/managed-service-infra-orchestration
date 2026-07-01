from projects.model import Project
from sqlalchemy.orm import Session
from database.db import get_db
from user.model import User
from fastapi import HTTPException
class ProjectRepo:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_project(self, project_data: dict) -> Project:
        user = self.db_session.query(User).filter_by(id=project_data['user_id']).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.no_of_projects >= 5:
            raise HTTPException(status_code=400, detail="User has reached the maximum number of allowed projects (5).")
        new_project = Project(user_id=project_data['user_id'], slug=project_data['slug'], type=project_data['type'], status=project_data['status'], gitURL=project_data['gitURL'], project_url=project_data['project_url'])
        self.db_session.add(new_project)
        user.no_of_projects += 1
        try:
            self.db_session.commit()
            self.db_session.refresh(new_project)
            return new_project
        except Exception as e:
            self.db_session.rollback()
            raise e

    def get_project_by_slug(self, project_slug: str):
        return self.db_session.query(Project).filter_by(slug=project_slug).first()

    def update_project(self, project_slug: str, update_data: dict):
        project = self.get_project_by_slug(project_slug)
        if project:
            for key, value in update_data.items():
                setattr(project, key, value)
            self.db_session.commit()
        return project

    def delete_project(self, project_id):
        project = self.get_project(project_id)
        if project:
            self.db_session.delete(project)
            self.db_session.commit()
        return project
    
    
# session = next(get_db())
# project_repo = ProjectRepo(db_session=session)