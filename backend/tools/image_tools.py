import base64
import mimetypes
from pathlib import Path
from groq import AsyncGroq
from backend.config import PROJECT_ROOT, VISION_MODEL
from backend.utils.retry import async_llm_retry

client = AsyncGroq()


# ---------------------------------
# Retryable internal call
# ---------------------------------

async def _call_vision(messages: list) -> str:
    """Async vision API call with retry."""
    async def _invoke():
        completion = await client.chat.completions.create(
            model=VISION_MODEL,
            messages=messages,
            temperature=0
        )
        return completion.choices[0].message.content

    return await async_llm_retry(_invoke)


# ---------------------------------
# Function
# ---------------------------------

async def image_analyser(file_path: str, query: str = "Describe this image in detail.") -> dict:
    """Analyze an image using a vision model."""
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path = path.resolve()

        if not path.exists():
            return {"success": False, "error": f"Image file not found: {path}"}

        mime_type, _ = mimetypes.guess_type(path)
        if mime_type is None:
            mime_type = "image/jpeg"

        # File I/O offloaded to thread — keeps event loop free
        import asyncio
        image_b64 = await asyncio.to_thread(
            lambda: base64.b64encode(path.read_bytes()).decode("utf-8")
        )

        image_url = f"data:{mime_type};base64,{image_b64}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": query},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]

        analysis = await _call_vision(messages)

        return {
            "success": True,
            "file_path": str(path),
            "analysis": analysis
        }

    except Exception as e:
        return {"success": False, "error": str(e)}