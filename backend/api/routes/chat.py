import uuid
import json
import asyncio
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from langgraph.types import Command

from backend.api.schemas import (
    ChatRequest, ChatResponse,
    ResetRequest, ResetResponse
)
from fastapi import APIRouter, HTTPException, Request, Depends
from backend.api.dependencies import get_current_user

router = APIRouter()


# ---------------------------------
# Node → human readable status
# ---------------------------------

NODE_MESSAGES = {
    "classify_files":  "Classifying uploaded documents...",
    "planner":         "Planning research strategy...",
    "executor_worker": "Extracting content from sources...",
    "url_router":      "Resolving references and links...",
    "generate":        "Synthesizing findings...",
    "clarification":   "Need more context...",
    "give_up":         "Could not resolve research query.",
}


# ---------------------------------
# Helpers
# ---------------------------------

def build_initial_state(request: ChatRequest,user_id: str) -> dict:
    return {
        "query": request.query,
        "user_id": user_id,
        "uploaded_files": request.file_paths,
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
        "final_answer": "",
        "conversation_summary": "",
        "summarized_message_count": 0
    }


def build_graph_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _sse(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    payload = json.dumps({"type": event_type, **data})
    return f"data: {payload}\n\n"


# ---------------------------------
# POST /chat  (non-streaming)
# ---------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest,req:Request,current_user: dict = Depends(get_current_user)):
    """
    Run the agent graph and return the final answer.
    Non-streaming — waits for full completion.
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    graph_config = build_graph_config(thread_id)
    graph=req.app.state.graph

    try:
        final_state = None

        async for event in graph.astream(
            build_initial_state(request, str(current_user["id"])),
            config=graph_config,
            stream_mode="values"
        ):
            final_state = event

        if not final_state:
            raise HTTPException(status_code=500, detail="Graph returned no state.")

        if not final_state.get("final_answer"):
            raise HTTPException(status_code=500, detail="Graph did not produce a final answer.")

        return ChatResponse(
            thread_id=thread_id,
            final_answer=final_state["final_answer"],
            task=final_state.get("task", "")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------
# POST /chat/stream  (SSE streaming)
# ---------------------------------

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest,req:Request,current_user: dict = Depends(get_current_user)):
    """
    Run the agent graph and stream node-level status
    events followed by the final answer token by token.
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    graph_config = build_graph_config(thread_id)
    graph=req.app.state.graph
    user_id = str(current_user["id"])

    async def event_stream():
        try:
            async for event in graph.astream(
                build_initial_state(request, user_id),
                config=graph_config,
                stream_mode="updates"
            ):
                for node_name, node_output in event.items():

                    # --- status event for every node ---
                    message = NODE_MESSAGES.get(node_name)
                    if message:
                        yield _sse("status", {
                            "node": node_name,
                            "message": message
                        })

                    # --- stream final answer token by token ---
                    if node_name in ("generate", "give_up"):
                        final_answer = node_output.get("final_answer", "")
                        if final_answer:
                            words = final_answer.split(" ")
                            for i, word in enumerate(words):
                                chunk = word if i == 0 else " " + word
                                yield _sse("token", {"content": chunk})
                                await asyncio.sleep(0)  # yield control to event loop

            # Check if the graph is interrupted at the clarification node
            state = await graph.aget_state(graph_config)
            if state.next and "clarification" in state.next:
                question = state.values.get("clarification_question", "")
                yield _sse("clarification", {
                    "node": "clarification",
                    "message": question,
                    "thread_id": thread_id
                })
            else:
                yield _sse("done", {"thread_id": thread_id})

        except Exception as e:
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


# ---------------------------------
# POST /chat/reset
# ---------------------------------

@router.post("/chat/reset", response_model=ResetResponse)
async def reset_chat(request: ResetRequest,req:Request):
    """
    Reset a session by issuing a new thread_id.
    Client uses the returned thread_id for subsequent requests.
    """
    try:
        new_thread_id = str(uuid.uuid4())
        return ResetResponse(
            thread_id=new_thread_id,
            success=True,
            message="Session reset. Use the new thread_id for your next request."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/chat/clarify")
async def chat_clarify(request: ChatRequest, req: Request,current_user: dict = Depends(get_current_user)):
    """
    Resume an interrupted graph with user's clarification response.
    thread_id is required — identifies the interrupted session.
    query is the user's clarification answer.
    """
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="thread_id required to resume clarification.")

    graph = req.app.state.graph
    graph_config = build_graph_config(request.thread_id)

    async def event_stream():
        try:
            async for event in graph.astream(
                Command(resume=request.query),
                config=graph_config,
                stream_mode="updates"
            ):
                for node_name, node_output in event.items():
                    message = NODE_MESSAGES.get(node_name)
                    if message:
                        yield _sse("status", {
                            "node": node_name,
                            "message": message
                        })

                    if node_name in ("generate", "give_up"):
                        final_answer = node_output.get("final_answer", "")
                        if final_answer:
                            words = final_answer.split(" ")
                            for i, word in enumerate(words):
                                chunk = word if i == 0 else " " + word
                                yield _sse("token", {"content": chunk})
                                await asyncio.sleep(0)

            # Check if the graph is interrupted again at the clarification node
            state = await graph.aget_state(graph_config)
            if state.next and "clarification" in state.next:
                question = state.values.get("clarification_question", "")
                yield _sse("clarification", {
                    "node": "clarification",
                    "message": question,
                    "thread_id": request.thread_id
                })
            else:
                yield _sse("done", {"thread_id": request.thread_id})

        except Exception as e:
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )