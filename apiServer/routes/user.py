from coolname import generate_slug
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from rabbitmq import rabbitmq
from database.db import get_db
from user.model import User
from security.authHelp import is_authenticated
from projects.service import project_list,project_exists
from projects.model import ProjectRequest
from fastapi import Request
from projects.repo import ProjectRepo
from config import config
from logger import publish_error
# from fastapi.security import OAuth2PasswordBearer

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

user_router = APIRouter()
# user_repo = UserRepository(session=Depends(get_db))
# project_repo = ProjectRepo(db_session=Depends(get_db))

@user_router.get("/users/{user_name}", )
async def get_user(user: User=Depends(is_authenticated), session: Session = Depends(get_db)):
    if not user.id:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }

@user_router.get("/project/list")
async def get_user_projects(user: User = Depends(is_authenticated), session: Session = Depends(get_db)):
    
    if not user.id:
        raise HTTPException(status_code=404, detail="Unauthorized: User ID not found")

    projects = project_list(session, user.id)
    return projects


@user_router.post("/project/deploy")
async def createProject(body: ProjectRequest, request: Request, session: Session = Depends(get_db), user: User = Depends(is_authenticated)):
    if not user.id:
        raise HTTPException(status_code=404, detail="Unauthorized: User ID not found")
    
    project_slug = body.slug if body.slug else generate_slug(2)

    print(f"Creating project with slug: {project_slug} for user ID: {user.id}")
    if body.type not in ['node', 'static']:
        raise HTTPException(status_code=400, detail="Invalid project type. Must be 'node' or 'static'.")
    print(f"Project type: {body.type}, Git URL: {body.gitURL}")
    if project_exists(session, project_slug):
        raise HTTPException(status_code=400, detail=f'Project with slug "{project_slug}" already exists.')
    print(f"Project slug '{project_slug}' is available for creation.")
    
    try:
        project_repo = ProjectRepo(db_session=session)
        project=project_repo.create_project({
            'user_id': user.id,
            'slug': project_slug,
            'type': body.type,
            'status': 'Queued',
            'gitURL': body.gitURL,
        'project_url': f'http://{project_slug}.{config.PROXY_BASE_PATH}'
        })
    
    except Exception as e:
        publish_error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error creating project.")


    await rabbitmq.publish({
        'gitURL': body.gitURL,
        'projectSlug': project_slug,
        'projectType': body.type
    })
    
    return {
        'status': 'Queued',
        'data': {
            'projectSlug': project_slug,
            'url': project.project_url,
            'projectStatus': project.status
        }
    }