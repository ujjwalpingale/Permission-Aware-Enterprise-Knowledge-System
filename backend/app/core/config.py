import os
import sys
import site
from pathlib import Path

# Ensure user site packages are accessible if using isolated virtual environment
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.insert(0, user_site)

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file from backend directory if present
env_dir = Path(__file__).resolve().parent.parent.parent
env_path = env_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Disable ChromaDB anonymized telemetry to avoid network timeouts during initialization
os.environ["ANONYMIZED_TELEMETRY"] = "False"

DEFAULT_CHROMA_DIR = str((env_dir / "chroma_db").resolve())


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"
    CHROMA_PERSIST_DIRECTORY: str = DEFAULT_CHROMA_DIR
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/enterprise_rag_db"
    JWT_SECRET_KEY: str = "supersecret_enterprise_rag_jwt_key_2026_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    TOP_K: int = 5

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
