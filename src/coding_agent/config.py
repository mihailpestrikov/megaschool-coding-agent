from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    github_token: str | None = None
    gemini_api_key: str
    github_repository: str | None = None
    github_app_id: str | None = None
    github_private_key: str | None = None
    github_webhook_secret: str | None = None
    max_iterations: int = 5
    gemini_model: str = "gemini-2.5-flash-lite"


def get_settings() -> Settings:
    return Settings()
