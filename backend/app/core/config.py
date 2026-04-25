from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sessional API"
    app_env: str = "development"
    allowed_origins_csv: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/sessional"
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 24
    processing_mode: str = "mock"  # mock | real
    llm_provider: str = "gemini"  # gemini | mock | openai | anthropic
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    hume_api_key: str | None = None
    hume_base_url: str = "https://api.hume.ai"
    hume_timeout_seconds: int = 60
    hume_poll_interval_seconds: int = 3
    hume_max_wait_seconds: int = 180
    hume_prosody_granularity: str = "utterance"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_csv.split(",") if origin.strip()]


settings = Settings()
