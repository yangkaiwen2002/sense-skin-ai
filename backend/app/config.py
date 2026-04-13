from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./skinsense.db"
    CLAUDE_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


settings = Settings()
