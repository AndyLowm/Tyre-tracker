from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

FILE_LOC = Path(__file__).resolve().parent.parent.parent
FILE_PATH = FILE_LOC/".env"

class Settings(BaseSettings):
    database_url: str
    model_config = SettingsConfigDict(
        env_file=FILE_PATH,
        env_file_encoding="utf-8"
    )

settings = Settings()