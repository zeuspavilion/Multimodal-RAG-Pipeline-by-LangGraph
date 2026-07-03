from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from pathlib import Path


def find_env_file() -> Path | str:
    start_dir = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    for parent in [start_dir] + list(start_dir.parents):
        env_path = parent / ".env"
        if env_path.exists():
            return env_path
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GROQ_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    HF_TOKEN: str = ""
    LANGCHAIN_API_KEY: str = ""
    LANGSMITH_ENDPOINT: str = ""
    NEON_DATABASE_URL: str = ""
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # Deployment
    ENVIRONMENT: str = "development"  # "development" | "production"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8501"
    
    @model_validator(mode="after")
    def check_required_keys(self):
        required = {
            "GROQ_API_KEY": self.GROQ_API_KEY,
            "TAVILY_API_KEY": self.TAVILY_API_KEY,
            "HF_TOKEN": self.HF_TOKEN,
            "NEON_DATABASE_URL": self.NEON_DATABASE_URL,
            "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
        }
        missing = [k for k, v in required.items() if not v or v == "None"]
        if missing:
            raise ValueError(
                f"\n\n[CONFIG ERROR] Missing required API keys: {missing}\n"
                f"Add them to your .env file and restart.\n"
            )
        return self


try:
    settings = Settings()
except Exception as e:
    raise SystemExit(e)


import os
os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY
os.environ["HF_TOKEN"] = settings.HF_TOKEN
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
os.environ["LANGCHAIN_TRACING_V2"] = "true" if settings.LANGCHAIN_API_KEY else "false"
os.environ["LANGSMITH_PROJECT"] = "Multimodal agent trace5"

# HF mirror is only needed in restricted networks (dev/local).
# In production Docker, the model is pre-downloaded at build time.
if settings.ENVIRONMENT == "development":
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"


# ---------------------------------
# Models
# ---------------------------------

PLANNER_MODEL = "openai/gpt-oss-120b"
GENERATOR_MODEL = "openai/gpt-oss-120b"
INTENT_CLASSIFIER_MODEL = "openai/gpt-oss-20b"
SUMMARIZER_MODEL = "openai/gpt-oss-120b"
AUDIO_MODEL = "whisper-large-v3-turbo"
VISION_MODEL = "qwen/qwen3.6-27b"


# ---------------------------------
# Audio chunking
# ---------------------------------

MAX_CHUNK_MB = 20
MAX_WORKERS = 4


# ---------------------------------
# Summarizer limits
# ---------------------------------

SUMMARIZER_TOKEN_LIMIT = 5000
CHARS_PER_TOKEN = 4
CHAR_LIMIT = SUMMARIZER_TOKEN_LIMIT * CHARS_PER_TOKEN


# ---------------------------------
# Embeddings (lazy loaded)
# ---------------------------------

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            print("[startup] Attempting to load HuggingFaceEmbeddings...")
            _embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"local_files_only": False}
            )
            # Test query to check if loading was successful
            _embeddings.embed_query("test")
            print("[startup] HuggingFaceEmbeddings loaded successfully.")
        except Exception as e:
            print(f"[Warning] Failed to load HuggingFaceEmbeddings ({e}). Falling back to local MockEmbeddings...")
            from langchain_core.embeddings import Embeddings
            import hashlib
            import random
            
            class MockEmbeddings(Embeddings):
                def embed_documents(self, texts: list[str]) -> list[list[float]]:
                    results = []
                    for text in texts:
                        # Seed based on text hash to produce deterministic output
                        seed = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % (2**32)
                        random.seed(seed)
                        results.append([random.uniform(-1, 1) for _ in range(384)])
                    return results

                def embed_query(self, text: str) -> list[float]:
                    return self.embed_documents([text])[0]
            
            _embeddings = MockEmbeddings()
            print("[startup] MockEmbeddings initialized.")
    return _embeddings


# ---------------------------------
# Embedding dimension
# ---------------------------------

EMBEDDING_DIMENSION = 384


# ---------------------------------
# Test user (replace with real auth later)
# ---------------------------------

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


# ---------------------------------
# Path resolution
# ---------------------------------

if "__file__" in globals():
    PROJECT_ROOT = Path(__file__).resolve().parent
else:
    cwd = Path.cwd()
    PROJECT_ROOT = cwd.parent if cwd.name == "notebooks" else cwd

# ---------------------------------
# Neon connection URL (asyncpg format)
# ---------------------------------

NEON_DATABASE_URL = settings.NEON_DATABASE_URL

# asyncpg requires postgresql+asyncpg:// scheme
NEON_ASYNC_URL = NEON_DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
).replace(
    "postgres://", "postgresql+asyncpg://"
)

UPSTASH_REDIS_REST_URL = settings.UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN = settings.UPSTASH_REDIS_REST_TOKEN
JWT_SECRET_KEY = settings.JWT_SECRET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
JWT_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES

# ---------------------------------
# Deployment settings
# ---------------------------------

ENVIRONMENT = settings.ENVIRONMENT
# Comma-separated list of allowed CORS origins, parsed at startup
CORS_ORIGINS: list[str] = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]