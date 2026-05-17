import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings 
from fastapi.templating import Jinja2Templates

load_dotenv()
templates = Jinja2Templates("client")

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ["DATABASE_URL"]
    JWT_KEY: str = os.environ["JWT_KEY"]
    ACCESS_TOKEN_EXPIRES: int = int(os.environ["ACCESS_TOKEN_EXPIRES"])
    REFRESH_TOKEN_EXPIRES: int = int(os.environ["REFRESH_TOKEN_EXPIRES"])
    JWT_ALG: str = os.environ["JWT_ALG"]
    # SECRET_KEY: str = os.environ["SECRET_KEY"]
    # SMTP_SERVER: str = os.environ["SMTP_SERVER"]
    # SMTP_PORT: int = int(os.environ["SMTP_PORT"])
    # SMTP_USERNAME: str = os.environ["SMTP_USERNAME"]
    MAIL_PASSWORD: str = os.environ["MAIL_PASSWORD"]
    MAIL_FROM: str = os.environ["MAIL_FROM"]
    MAIL_FROM_NAME: str = os.environ["MAIL_FROM_NAME"]

    GOOGLE_CLIENT_ID: str = os.environ["GOOGLE_CLIENT_ID"]
    GOOGLE_CLIENT_SECRET: str = os.environ["GOOGLE_CLIENT_SECRET"]
    GOOGLE_REDIRECT_URI: str = os.environ["GOOGLE_REDIRECT_URI"]
    
    # AI Configuration
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    SERPER_API_KEY: str = os.environ.get("SERPER_API_KEY", "")


settings = Settings()