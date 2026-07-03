from langchain_tavily import TavilySearch
from backend.utils.retry import async_api_retry


# ---------------------------------
# Retryable internal call
# ---------------------------------

async def _tavily_search(query: str):
    """Async Tavily search with retry."""
    async def _invoke():
        tavily = TavilySearch(max_results=5)
        return await tavily.ainvoke({"query": query})

    return await async_api_retry(_invoke)


# ---------------------------------
# Functions
# ---------------------------------

async def web_search(query: str) -> dict:
    """Search the web for up-to-date information."""
    try:
        results = await _tavily_search(query)
        return {
            "success": True,
            "query": query,
            "results": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def url_classifier(url: str) -> dict:
    """
    Classify URL type.
    Pure string matching — stays sync, no network call.
    """
    if "youtube.com" in url or "youtu.be" in url:
        return {"success": True, "url": url, "type": "youtube"}
    return {"success": True, "url": url, "type": "website"}