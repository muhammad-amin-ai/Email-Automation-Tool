from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "email_automation_db"

    SECRET_KEY: str = "change-me-to-a-long-random-secret-string-at-least-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    BREVO_API_KEY: str = ""
    EMAIL_FROM: str = ""
    EMAIL_FROM_NAME: str = "Email Platform"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: int = 60

    SCHEDULER_ENABLED: bool = True
    SCHEDULER_INTERVAL_SECONDS: int = 60
    SCHEDULER_BATCH_SIZE: int = 50

    FRONTEND_URL: str = "http://localhost:5173"
    API_PREFIX: str = "/api"

    # Default sender/business profile — used automatically for any user who
    # hasn't set their own profile via PATCH /auth/me. Set these once here
    # (in .env) so emails work out of the box without a manual API call.
    DEFAULT_SENDER_NAME: str = ""
    DEFAULT_SENDER_TITLE: str = ""
    DEFAULT_COMPANY_NAME: str = ""
    DEFAULT_SENDER_PHONE: str = ""
    # Overrides the {{sender_email}} shown in emails, regardless of which
    # account is logged in (useful when the login account is a test/dev
    # email but outgoing emails should show a real contact address).
    DEFAULT_SENDER_EMAIL: str = ""
    DEFAULT_WEBSITE_URL: str = ""

    APP_NAME: str = "Email Automation Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()