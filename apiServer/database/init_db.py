from logger import publish_log
from database.db import Base, engine
from user.model import User
from projects.model import Project

def create_tables():
    Base.metadata.create_all(bind=engine)
    publish_log("DB connected")

    