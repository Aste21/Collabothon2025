from pathlib import Path

from llama_stack_client import LlamaStackClient, RAGDocument

from config import get_settings

settings = get_settings()


def load_aws_kb_text() -> str:
    """Read the AWS knowledge base markdown file."""
    return Path(settings.kb_path).read_text(encoding="utf-8")


def seed_aws_kb() -> None:
    """Insert the AWS knowledge base into the configured vector DB."""
    client = LlamaStackClient(base_url=settings.base_url)

    kb_text = load_aws_kb_text()

    document = RAGDocument(
        document_id="aws_knowledge_base_001",
        content=kb_text,
        mime_type="text/markdown",
        metadata={"source": "aws_kb"},
    )

    client.tool_runtime.rag_tool.insert(
        documents=[document],
        vector_db_id=settings.vector_db_id,
        chunk_size_in_tokens=settings.rag_chunk_size_tokens,
    )

    print(f"Inserted AWS KB into vector DB '{settings.vector_db_id}'.")


if __name__ == "__main__":
    seed_aws_kb()
