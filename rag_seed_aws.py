from pathlib import Path

from llama_stack_client import LlamaStackClient, RAGDocument

# ==== CONFIG – dostosuj do swojego środowiska ====
BASE_URL = "http://lsd-llama-milvus-inline-service:8321/"
VECTOR_DB_ID = "form_helper_db"  # UŻYJ TEGO SAMEGO ID, KTÓRY ZAREJESTROWAŁEŚ W NOTEBOOKU

# Spróbuj użyć __file__ (gdy to jest normalny .py), a w notebooku fallback na cwd
try:
    base_path = Path(__file__).parent
except NameError:
    base_path = Path.cwd()

AWS_KB_PATH = base_path / "aws_architecture_kb.md"
# ================================================


def load_aws_kb_text() -> str:
    """Read the AWS knowledge base markdown file."""
    return AWS_KB_PATH.read_text(encoding="utf-8")


def seed_aws_kb() -> None:
    """Insert the AWS knowledge base into the configured vector DB.

    Steps:
    1) Create LlamaStack client for the given BASE_URL.
    2) Read the aws_knowledge_base.md file.
    3) Wrap it into a single RAGDocument.
    4) Use rag_tool.insert to index it in the given VECTOR_DB_ID.
    """
    client = LlamaStackClient(base_url=BASE_URL)

    kb_text = load_aws_kb_text()

    document = RAGDocument(
        document_id="aws_knowledge_base_001",
        content=kb_text,
        mime_type="text/markdown",
        metadata={"source": "aws_kb"},
    )

    client.tool_runtime.rag_tool.insert(
        documents=[document],
        vector_db_id=VECTOR_DB_ID,
        chunk_size_in_tokens=300,
    )

    print(f"Inserted AWS KB into vector DB '{VECTOR_DB_ID}'.")


if __name__ == "__main__":
    seed_aws_kb()
