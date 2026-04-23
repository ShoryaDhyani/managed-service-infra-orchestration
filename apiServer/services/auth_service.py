from sqlalchemy.orm import Session
from models.user import User


class AuthService:
    @staticmethod
    def upsert_github_user(db: Session, github_user: dict, token: str):
        user = db.query(User).filter(
            User.github_id == str(github_user["id"])
        ).first()

        if user:
            user.username = github_user["login"]
            user.avatar_url = github_user.get("avatar_url")
            user.access_token = token
        else:
            user = User(
                github_id=str(github_user["id"]),
                username=github_user["login"],
                email=github_user.get("email"),
                avatar_url=github_user.get("avatar_url"),
                access_token=token,
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        return user