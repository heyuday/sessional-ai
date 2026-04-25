from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sessional API"
    app_env: str = "development"
    allowed_origins_csv: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = "postgresql+psycopg://postgres:postgres@127.0.0.1:5432/sessional"
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 24

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins_csv.split(",") if origin.strip()]


settings = Settings()
