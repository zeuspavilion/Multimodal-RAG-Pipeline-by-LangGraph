from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
import operator

def merge_extracted_contents(old: dict, new: dict) -> dict:
    if new and new.get("clear"):
        return {"files": {}}
    old_files = old.get("files", {}) if old else {}
    new_files = new.get("files", {}) if new else {}
    return {"files": {**old_files, **new_files}}


class AgentState(TypedDict):
    query: str
    user_id: str
    uploaded_files: list[str]
    pdf_files: list[str]
    audio_files: list[str]
    image_files: list[str]
    task: str
    required_actions: list[dict]
    needs_clarification: bool
    clarification_question: str
    clarification_attempts: int
    awaiting_clarification: bool
    extracted_contents: Annotated[dict, merge_extracted_contents]
    urls_found: Annotated[list[str], lambda old, new: list(set(new))]
    youtube_urls: list[str]
    web_urls: list[str]
    messages: Annotated[list[BaseMessage], operator.add]
    final_answer: str
    conversation_summary: str
    summarized_message_count: int


class Action(BaseModel):
    action_id: str | None = None
    worker: str   # "pdf_worker" | "audio_worker" | "image_worker" | "web_worker"
    operation: str  # "full_document" | "retrieve" | "transcribe" | "analyze" | "search"
    file_path: str | None = None
    query: str | None = None


class PlannerDecision(BaseModel):
    task: str
    required_actions: list[Action]
    needs_clarification: bool
    clarification_question: str


class FileContent(TypedDict, total=False):
    type: str=Field(description="file type: pdf/audio/image")
    content: str=Field(description="Full pdf text")
    transcript: str=Field(description="Audio transcription")
    analysis: str=Field(description="Vision model output")
    retrieved_context: list[str]=Field(description="Chunks from retriever")
    urls: list[str]=Field(description="URLs extracted from PDF")
    source_url: str
    error: str


class ExtractedContents(TypedDict):
    files: dict[str, FileContent]


class ExecutorState(TypedDict):
    query: str
    task: str
    required_actions: list[Action]
    extracted_contents: ExtractedContents
    urls_found: list[str]