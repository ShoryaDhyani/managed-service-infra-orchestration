from os import access
from fastapi.exceptions import HTTPException
import jwt

from datetime import datetime, timedelta

from config import config
from database.db import get_db
from user.repo import UserRepository
from sqlalchemy.orm import Session
from user.model import UserCreate, UserLogin
from security.authHelp import JWTAuthHelper
from security.hashing import HashingService



class UserService:
    def __init__(self, session: Session):
        self.settings = config
        self.__session = session
        self.__userRepo = UserRepository(session=session)


    def signup(self, username: str, password: str, email: str) -> dict:
        if self.__userRepo.check_user_exists(username):
            raise HTTPException(status_code=400, detail="Username already exists")
        if self.__userRepo.check_email_exists(email):
            raise HTTPException(status_code=400, detail="Email already exists")
        
        user_data = UserCreate(username=username, password=password, email=email)
        new_user = self.__userRepo.create_user(user_data)
        token = self.create_tokens(new_user)
        return {
            "token": token,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email
            }
        } 
    
    def login(self, password: str, username  : str) ->dict:
        user = self.__userRepo.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not HashingService.verify_password(password, str(user.hashed_password)):
            raise HTTPException(status_code=401, detail="Invalid credentials")  
        
        token=self.create_tokens(user)
        return {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        } 

    def create_tokens(self, user) -> str:
        access_token=JWTAuthHelper.create_jwt({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })
        return access_token 
    