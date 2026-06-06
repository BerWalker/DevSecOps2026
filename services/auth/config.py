import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or os.getenv(
        "AUTH_DATABASE_URL", ""
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    JWT_ALGORITHM = "HS256"

    @staticmethod
    def validate(required_for_runtime: bool = True) -> None:
        if not required_for_runtime:
            return
        missing = []
        if not Config.SQLALCHEMY_DATABASE_URI:
            missing.append("DATABASE_URL")
        if not Config.JWT_SECRET_KEY:
            missing.append("JWT_SECRET_KEY")
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
