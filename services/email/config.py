import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
    GMAIL_FROM = os.getenv("GMAIL_FROM", "")
    GMAIL_USER = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

    @staticmethod
    def validate(required_for_runtime: bool = True) -> None:
        if not required_for_runtime:
            return
        missing = []
        if not Config.INTERNAL_API_KEY:
            missing.append("INTERNAL_API_KEY")
        if not Config.GMAIL_FROM:
            missing.append("GMAIL_FROM")
        if not Config.GMAIL_USER:
            missing.append("GMAIL_USER")
        if not Config.GMAIL_APP_PASSWORD:
            missing.append("GMAIL_APP_PASSWORD")
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
