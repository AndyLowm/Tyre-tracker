from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

FILE_LOC = Path(__file__).resolve().parent.parent.parent
FILE_PATH = FILE_LOC/".env"

logging.basicConfig(
    filename= FILE_LOC/"app_security_log.txt",
    level=logging.INFO,
    format= "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - [ENDPOINT]: %(message)s"
)

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    database_url: str
    jwt_key: str
    jwt_algo: str
    model_config = SettingsConfigDict(
        env_file=FILE_PATH,
        env_file_encoding="utf-8"
    )

settings = Settings()