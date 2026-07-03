sys.path.append(str(Path(__file__).resolve().parent.parent))

from langgraph.checkpoint.memory import MemorySaver
import uuid
from langgraph.types import Command
import sys
from pathlib import Path
import asyncio

from backend import config as app_config
from backend.graph import graph_builder


graph = graph_builder.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["clarification"]
)
UPLOAD_DIR = app_config.PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)



def run(query: str, file_paths: list[str], thread_id: str | None = None):
    return asyncio.run(_run_async(query, file_paths, thread_id))

async def _run_async(query: str, file_paths: list[str], thread_id: str | None = None):
    thread_id = thread_id or str(uuid.uuid4())
    graph_config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "query": query,
        "uploaded_files": file_paths,
        "pdf_files": [],
        "audio_files": [],
        "image_files": [],
        "task": "",
        "required_actions": [],
        "needs_clarification": False,
        "clarification_attempts": 0,
        "clarification_question": "",
        "awaiting_clarification": False,
        "extracted_contents": {"files": {}},
        "urls_found": [],
        "messages": [],
        "final_answer": ""
    }

    print(f"[Session: {thread_id}]")

    async for event in graph.astream(initial_state, config=graph_config):
        print(event)
        print("=" * 80)

    while True:
        snapshot = await graph.aget_state(graph_config)
        if not snapshot.next:
            break

        user_response = input("\nAgent needs clarification.\nYou: ").strip()

        async for event in graph.astream(
            Command(resume=user_response),
            config=graph_config
        ):
            print(event)
            print("=" * 80)

    return thread_id

if __name__ == "__main__":
    run(
        query="summarise the yt video if any yt link is present in the pdf.",
        file_paths=[str(UPLOAD_DIR / "pdf_containing_url.pdf")]
    )