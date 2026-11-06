from typing import Literal
from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./skinsense.db"
    CLAUDE_API_KEY: str = ""
    AI_PROVIDER: Literal["anthropic", "openai"] = "anthropic"
    AI_API_KEY: str = ""
    AI_BASE_URL: str = ""
    AI_MODEL: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    BUFF_COOKIE: str = ""
    BUFF_GOODS_IDS: dict[str, PositiveInt] = Field(default_factory=dict)
    ENABLE_MARKET_SYNC: bool = False
    BUFF_USER_AGENT: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    BUFF_REFERER: str = "https://buff.163.com/market/"

    # RAG hybrid retrieval
    RAG_EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    RAG_ENABLE_FAISS: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
