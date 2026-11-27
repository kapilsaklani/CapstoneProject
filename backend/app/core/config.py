import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ML_MODELS_DIR = BASE_DIR / "trained_models"
if not ML_MODELS_DIR.exists():
    ML_MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "trained_models"

class Settings:
    PROJECT_NAME: str = "MedAssist AI"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "medassist-ai-secret-key-change-later")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ML_MODELS_DIR: Path = ML_MODELS_DIR
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{Path(__file__).resolve().parent.parent.parent / 'medassist_ai.db'}"
    )

settings = Settings()
