from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./skinsense.db"
    CLAUDE_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    BUFF_COOKIE: str = ""
    BUFF_USER_AGENT: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    BUFF_REFERER: str = "https://buff.163.com/market/"

    class Config:
        env_file = ".env"


settings = Settings()
