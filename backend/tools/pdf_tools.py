import re
import asyncio
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from backend.config import PROJECT_ROOT
from backend.db.vector_store import store_document_chunks, retrieve_similar_chunks


async def pdf_parser(file_path: str) -> dict:
    """Parse PDF and extract full text + URLs."""
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path = path.resolve()

        if not path.exists():
            return {"success": False, "error": f"PDF not found: {path}"}

        def _parse():
            loader = PyPDFLoader(str(path))
            docs = loader.load()
            full_text = "\n\n".join(doc.page_content for doc in docs)
            urls = list(set(re.findall(r"https?://[^\s<>\"]+", full_text)))
            return docs, full_text, urls

        docs, full_text, urls = await asyncio.to_thread(_parse)

        return {
            "success": True,
            "file_path": str(path),
            "file_name": path.name,
            "num_pages": len(docs),
            "content": full_text,
            "urls": urls
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def document_retriever(
    document_content: str,
    file_name: str,
    query: str,
    user_id: str,
    k: int = 5,
) -> dict:
    """
    Store document chunks in pgvector on first call (idempotent),
    then retrieve top-k relevant chunks for the query.
    Replaces the old FAISS rebuild-on-every-query pattern.
    """
    try:
        file_hash = await store_document_chunks(
            content=document_content,
            file_name=file_name,
            user_id=user_id
        )

        chunks = await retrieve_similar_chunks(
            query=query,
            file_hash=file_hash,
            k=k,
            user_id=user_id
        )

        return {
            "success": True,
            "retrieved_context": chunks
        }

    except Exception as e:
        return {"success": False, "error": str(e)}