from projects.model import Project
from user.model import User
from database.db import get_db

def project_exists(db, slug):
    return db.query(Project).filter(Project.slug == slug).first() is not None

def project_list(db, user_id):
    projects=db.query(Project).filter(Project.user_id == user_id).all()
    return projects

def project_status(db, project_id):
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.status if project else None

def update_project_status( project_slug, new_status,db=get_db()):
    project = db.query(Project).filter(Project.slug == project_slug).first()
    if project:
        project.status = new_status
        db.commit()
        db.refresh(project)
        return project
    return None