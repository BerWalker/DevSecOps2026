import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or os.getenv(
        "ANALYTICS_DATABASE_URL", ""
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM = "HS256"
    CAMPAIGN_SERVICE_URL = os.getenv(
        "CAMPAIGN_SERVICE_URL", "http://campaign:5002"
    ).rstrip("/")
    INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
    GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway").rstrip("/")

    @staticmethod
    def validate(required_for_runtime: bool = True) -> None:
        if not required_for_runtime:
            return
        missing = []
        if not Config.SQLALCHEMY_DATABASE_URI:
            missing.append("DATABASE_URL")
        if not Config.JWT_SECRET_KEY:
            missing.append("JWT_SECRET_KEY")
        if not Config.INTERNAL_API_KEY:
            missing.append("INTERNAL_API_KEY")
        if not Config.GATEWAY_URL:
            missing.append("GATEWAY_URL")
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
