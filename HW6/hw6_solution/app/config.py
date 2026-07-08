from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "data236_hw6"

    CHAT_MODEL: str = "llama3.2:3b"
    EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT_SECS: int = 45

    SHORT_TERM_N: int = 8
    EPISODIC_TOP_K: int = 4
    SUMMARIZE_EVERY_USER_MSGS: int = 4
    DEFAULT_SESSION_ID: str = "default"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
