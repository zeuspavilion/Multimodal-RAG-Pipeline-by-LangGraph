from langchain_text_splitters import RecursiveCharacterTextSplitter
from groq import AsyncGroq
from backend.config import CHAR_LIMIT, SUMMARIZER_MODEL
from backend.utils.retry import async_llm_retry
from backend.db.cache import get_cached_llm_response, set_cached_llm_response

client = AsyncGroq()


# ---------------------------------
# Retryable internal call
# ---------------------------------

async def _call_llm(messages: list, max_tokens: int) -> str:
    # Build cache key from the user message content only
    prompt = messages[-1]["content"]

    cached = await get_cached_llm_response(prompt)
    if cached:
        return cached

    async def _invoke():
        response = await client.chat.completions.create(
            model=SUMMARIZER_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0
        )
        return response.choices[0].message.content

    result = await async_llm_retry(_invoke)
    await set_cached_llm_response(prompt, result)
    return result


# ---------------------------------
# Summarizer
# ---------------------------------

async def map_reduce_summarizer(text: str, source_type: str = "document") -> dict:
    """
    Summarize arbitrarily large text using Map-Reduce.

    Splits text into chunks that fit the 8k context window,
    summarizes each chunk independently (MAP), then combines
    all chunk summaries into a final summary (REDUCE).

    Works for: PDF content, audio transcripts, YouTube transcripts,
    webpage content, or any large block of text.

    Args:
        text:        The raw text to summarize.
        source_type: Label for logging — 'pdf', 'audio', 'youtube', etc.
    """
    try:

        # -------------------------------------------------------
        # Short enough — summarize directly in one shot
        # -------------------------------------------------------
        if len(text) <= CHAR_LIMIT:
            summary = await _call_llm(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise summarizer. "
                            "Return a concise but complete summary."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Summarize the following {source_type}:\n\n{text}"
                    }
                ],
                max_tokens=800
            )
            return {
                "success": True,
                "strategy": "direct",
                "num_chunks": 1,
                "summary": summary
            }

        # -------------------------------------------------------
        # Too large — MAP phase: chunk and summarize each piece
        # -------------------------------------------------------
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHAR_LIMIT,
            chunk_overlap=800
        )
        chunks = splitter.split_text(text)

        # MAP — all chunks summarized concurrently
        import asyncio
        map_tasks = [
            _call_llm(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise summarizer. "
                            "Summarize this section, preserving "
                            "key facts, names, numbers, and decisions."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Summarize section {i+1} of {len(chunks)} "
                            f"from a {source_type}:\n\n{chunk}"
                        )
                    }
                ],
                max_tokens=600
            )
            for i, chunk in enumerate(chunks)
        ]

        chunk_summaries = await asyncio.gather(*map_tasks)

        # -------------------------------------------------------
        # REDUCE phase: combine chunk summaries into final summary
        # -------------------------------------------------------
        combined = "\n\n---\n\n".join(
            f"[Section {i+1}]\n{s}"
            for i, s in enumerate(chunk_summaries)
        )

        final_summary = await _call_llm(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise summarizer. "
                        "You will receive a list of section summaries "
                        "from a larger document. Synthesize them into "
                        "one coherent, complete final summary. Do not "
                        "repeat yourself. Connect ideas across sections."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Combine these {len(chunks)} section summaries "
                        f"from a {source_type} into one final summary:\n\n"
                        f"{combined}"
                    )
                }
            ],
            max_tokens=1000
        )

        return {
            "success": True,
            "strategy": "map_reduce",
            "num_chunks": len(chunks),
            "chunk_summaries": list(chunk_summaries),
            "summary": final_summary
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }