from fastapi.params import Depends
import jwt
from database.db import get_db
from config import config
from datetime import datetime, timedelta, timezone
from fastapi import Depends, Request, HTTPException
from user.model import User, UserToken
from user.repo import user_repo
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
JWT_SECRET_KEY = config.JWT_SECRET_KEY
JWT_ALGORITHM = config.JWT_ALGORITHM
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

class JWTAuthHelper(object):
    @staticmethod
    def create_jwt(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_jwt(token: str) -> dict:
        try:
            payload = jwt.decode(token, key=JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        

    @staticmethod
    def get_user_from_jwt(token: str) -> User:
        payload = JWTAuthHelper.verify_jwt(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = payload.get("id")
        return user_repo.get_user_by_id(user_id)

jwt_helper = JWTAuthHelper()

def is_authenticated(request: Request, session: Session = Depends(get_db)) -> User:
    token = request.headers.get("Authorization")
    # print("Token from request headers:", token)  # Debugging line
    token = token.split(" ")[1] if token and " " in token else None
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    user=jwt_helper.get_user_from_jwt(token)

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user