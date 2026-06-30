from fastapi import APIRouter
from security.authHelp import is_authenticated
from user.repo import UserRepository
from user.model import User, UserCreate, UserLogin 
from sqlalchemy.orm import Session
from database.db import get_db
from fastapi import Depends
from user.service import UserService
from fastapi.exceptions import HTTPException

auth_router = APIRouter()
@auth_router.post("/login")
async def login(login_data: UserLogin, session: Session=Depends(get_db)):
    userRepo = UserRepository(session=session)
    userSer=UserService(session)
    user = userRepo.get_user_by_username(login_data.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return_data=userSer.login(login_data.password, login_data.username)
        return return_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise e

@auth_router.post("/register")
async def register(signup_data: UserCreate, session: Session=Depends(get_db)):


    userRepo = UserRepository(session=session)
    userSer=UserService(session)
    try:
        return_data=userSer.signup(signup_data.username, signup_data.password, signup_data.email)
        return return_data  
    except Exception as e:
        raise e

    return {"error": "User already exists"}

@auth_router.get("/logout")
async def logout(user: User = Depends(is_authenticated)):
    # Implementation for logout functionality
    pass
