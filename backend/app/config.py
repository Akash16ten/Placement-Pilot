"""Central configuration, read from environment / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")

    EMBEDDING_BACKEND: str = os.getenv("EMBEDDING_BACKEND", "auto").lower()  # auto | st | hash
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(ROOT / "data"))).resolve()
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
    ]
    MAX_UPLOAD_MB: int = 5

    KB_PATH: Path = Path(__file__).resolve().parent / "data" / "company_kb.json"
    SKILLS_PATH: Path = Path(__file__).resolve().parent / "data" / "skills.json"


settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
