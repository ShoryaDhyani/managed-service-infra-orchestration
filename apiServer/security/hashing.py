from bcrypt import hashpw, checkpw, gensalt 
from config import config

from datetime import datetime, timedelta

# Configure password hashing

class HashingService(object):
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for secure storage"""
        password_bytes = (password+config.PEPPER).encode('utf-8')
        return hashpw(password_bytes, gensalt()).decode('utf-8')
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        if checkpw((plain_password+config.PEPPER).encode('utf-8'), hashed_password.encode('utf-8')):
           return True
        return False 

    # @staticmethod
    # def get_password_hash(password: str) -> str:
    #     """Get the password hash for a given password"""
    #     password_bytes = (password+config.PEPPER).encode('utf-8')
    #     return hashpw(password_bytes, gensalt()).decode('utf-8')




hashing_service = HashingService()
