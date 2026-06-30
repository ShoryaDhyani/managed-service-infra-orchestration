from database.db import get_db
from user.model import User
from user.model import UserCreate
# from repository.base import BaseRepository
from security.hashing import hashing_service
from fastapi import Depends
from sqlalchemy.orm import Session


class UserRepository():
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def create_user(self, user_data: UserCreate) -> User:
        hashed_password=hashing_service.hash_password(user_data.password)
        new_user = User(username=user_data.username, email=user_data.email, hashed_password=hashed_password)
        self.session.add(new_user)
        try:
            self.session.commit()
            self.session.refresh(new_user)
            return new_user
        except Exception as e:
            self.session.rollback()
            raise e
    
    
    def check_user_exists(self, username: str) -> bool:
        return self.session.query(User).filter(User.username == username).first() is not None
    
    def check_email_exists(self, email: str) -> bool:
        return self.session.query(User).filter(User.email == email).first() is not None
    
    def get_user_by_username(self, username: str) -> User:
        user = self.session.query(User).filter(User.username == username).first()
        return user

    def get_user_by_id(self, user_id: int) -> User:
        return self.session.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> User:
        return self.session.query(User).filter(User.email == email).first()

session = next(get_db())
user_repo = UserRepository(session=session)