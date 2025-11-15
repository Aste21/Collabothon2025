import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

DEFAULT_FRONTEND_ORIGIN = "http://react-frontend-bieluchy-frontend.apps.cluster-qmfr5.qmfr5.sandbox265.opentlc.com"
DEFAULT_BASE_URL = "http://lsd-llama-milvus-inline-service-collabothon.apps.cluster-qmfr5.qmfr5.sandbox265.opentlc.com"
DEFAULT_MODEL_ID = "granite-31-8b"
DEFAULT_VECTOR_DB_ID = "form_helper_db"
DEFAULT_MAX_HISTORY_MESSAGES = 20
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_RAG_CHUNK_SIZE = 300
DEFAULT_PORT = 8080


@dataclass(frozen=True)
class Settings:
    base_url: str
    model_id: str
    vector_db_id: str
    max_history_messages: int
    llm_temperature: float
    kb_path: Path
    rag_chunk_size_tokens: int
    api_port: int
    frontend_origin: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    kb_env = os.getenv("AWS_KB_PATH")
    kb_path = Path(kb_env) if kb_env else PROJECT_ROOT / "aws_architecture_kb.md"

    return Settings(
        base_url=os.getenv("LLAMA_BASE_URL", DEFAULT_BASE_URL),
        model_id=os.getenv("LLAMA_MODEL_ID", DEFAULT_MODEL_ID),
        vector_db_id=os.getenv("VECTOR_DB_ID", DEFAULT_VECTOR_DB_ID),
        max_history_messages=int(
            os.getenv("MAX_HISTORY_MESSAGES", DEFAULT_MAX_HISTORY_MESSAGES)
        ),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", DEFAULT_LLM_TEMPERATURE)),
        kb_path=kb_path,
        rag_chunk_size_tokens=int(
            os.getenv("RAG_CHUNK_SIZE_TOKENS", DEFAULT_RAG_CHUNK_SIZE)
        ),
        api_port=int(os.getenv("PORT", DEFAULT_PORT)),
        frontend_origin=str(os.getenv("FRONTEND_ORIGIN", DEFAULT_FRONTEND_ORIGIN))
    )
