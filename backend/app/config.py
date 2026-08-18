from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://swarmshield:swarmshield@db:5432/swarmshield"
    frontend_url: str = "http://localhost:5173"
    jwt_secret: str = "development-only-change-me"
    admin_email: str = "admin@swarmshield.local"
    admin_password: str = "change-me-before-production"
    demo_mode: bool = True
    n8n_base_url: str = "http://n8n:5678"
    n8n_webhook_secret: str = "development-only-change-me"
    event_stream_poll_seconds: float = 1.0


settings = Settings()
