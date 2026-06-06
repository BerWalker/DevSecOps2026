import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM = "HS256"
    TRACKING_BASE_URL = os.getenv(
        "TRACKING_BASE_URL", "http://localhost:5000"
    ).rstrip("/")

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
