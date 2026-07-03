from pathlib import Path
from langchain_core.messages import HumanMessage


async def classify_and_route(state: dict) -> dict:
    """
    Classifies uploaded files and resets per-turn working state.
    extracted_contents and urls_found are cleared each turn so stale
    results from previous turns don't leak into the current generation.

    NOTE: This is intentional — extracted_contents is ephemeral working
    state, not conversation history. When you add a DB later, persist
    final_answer + query into the DB from generate_node, not extracted_contents.
    """
    result = {
        "pdf_files": [],
        "audio_files": [],
        "image_files": [],
        "extracted_contents": {"files": {}, "clear": True},
        "urls_found": [],
        "messages": [HumanMessage(content=state.get("query", ""))],
    }

    for file in state.get("uploaded_files", []):
        suffix = Path(file).suffix.lower()
        if suffix == ".pdf":
            result["pdf_files"].append(file)
        elif suffix in [".mp3", ".wav", ".m4a"]:
            result["audio_files"].append(file)
        elif suffix in [".jpg", ".jpeg", ".png"]:
            result["image_files"].append(file)

    return result