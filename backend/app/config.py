"""Configuration lue depuis les variables d'environnement ou le fichier .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./stagesonar.db"

    scrape_interval_hours: int = 6
    match_threshold: float = 0.2
    request_delay_seconds: float = 2.0
    user_agent: str = "StageSonarBot/0.1 (projet universitaire)"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    mail_from: str = ""

    frontend_url: str = "http://localhost:5173"


settings = Settings()
