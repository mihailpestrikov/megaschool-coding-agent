from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    github_token: str | None = None
    github_repository: str | None = None
    github_app_id: str | None = None
    github_private_key: str | None = None
    github_webhook_secret: str | None = None
    max_iterations: int = 2

    llm_model: str = "gemini/gemini-2.5-flash"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    xai_api_key: str | None = None


def get_settings() -> Settings:
    return Settings()
