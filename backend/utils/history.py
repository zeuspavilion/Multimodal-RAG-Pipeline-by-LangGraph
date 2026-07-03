import logging
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from backend.config import SUMMARIZER_MODEL
from backend.utils.retry import async_llm_retry
from backend.db.cache import get_cached_llm_response, set_cached_llm_response

logger = logging.getLogger(__name__)

RECENT_TURNS_TO_KEEP = 3

def get_recent_history_str(messages: list[BaseMessage]) -> str:
    """
    Format up to RECENT_TURNS_TO_KEEP turns of conversation history from state['messages'].
    The last message is the query/answer currently being processed.
    We exclude the last message to get the prior context.
    """
    if not messages:
        return ""
        
    prior_messages = messages[:-1]
    
    limit = 2 * RECENT_TURNS_TO_KEEP
    recent_messages = prior_messages[-limit:] if limit > 0 else []
    
    history_lines = []
    for msg in recent_messages:
        role = "User" if msg.type == "human" else "Assistant"
        history_lines.append(f"{role}: {msg.content}")
        
    return "\n\n".join(history_lines)


async def update_conversation_summary_if_needed(
    messages: list[BaseMessage],
    existing_summary: str,
    summarized_count: int
) -> tuple[str, int]:
    """
    Incrementally updates the conversation summary when state['messages'] exceeds the verbatim window.
    Returns: (new_summary_string, new_summarized_count)
    """
    if not messages:
        return "", 0

    # Limit for verbatim window: current query + RECENT_TURNS_TO_KEEP turns
    limit = 2 * RECENT_TURNS_TO_KEEP + 1
    
    if len(messages) <= limit:
        return existing_summary, summarized_count

    # The messages that should be part of the summary are anything before the window
    old_messages = messages[:-limit]
    total_old_count = len(old_messages)

    if total_old_count <= summarized_count:
        return existing_summary, summarized_count

    # Identify the new messages that have aged out since the last summary
    new_old_messages = old_messages[summarized_count:]
    if not new_old_messages:
        return existing_summary, summarized_count

    # Format the new dialogue turns as text
    new_turns_text = ""
    for msg in new_old_messages:
        role = "User" if msg.type == "human" else "Assistant"
        new_turns_text += f"{role}: {msg.content}\n\n"

    # Build the prompt key/content
    prompt = f"""Existing Summary of Earlier Conversation:
{existing_summary or "None"}

New Dialogue Turns:
{new_turns_text}

Update the summary to incorporate the new dialogue turns. Ensure the result is cohesive, concise, and dense. Output only the updated summary."""

    try:
        # Check cache first
        cached = await get_cached_llm_response(prompt)
        if cached:
            return cached, total_old_count

        # Call LLM with retry
        summarizer_llm = ChatGroq(model=SUMMARIZER_MODEL, temperature=0)
        
        async def _invoke():
            msgs = [
                SystemMessage(content=(
                    "You are a precise, concise research conversation assistant. "
                    "Your task is to update and maintain a running summary of a conversation, "
                    "incorporating new dialogue turns into the existing summary. "
                    "Keep the output extremely compact, dense, and focused on key facts, "
                    "concepts, papers discussed, and research directions. "
                    "Do not write a verbose narrative or include pleasantries."
                )),
                HumanMessage(content=prompt)
            ]
            response = await summarizer_llm.ainvoke(msgs)
            return response.content

        new_summary = await async_llm_retry(_invoke)
        
        # Set cache
        await set_cached_llm_response(prompt, new_summary)
        return new_summary, total_old_count

    except Exception as e:
        logger.warning(f"Error during incremental summarization: {e}. Falling back to previous summary.")
        return existing_summary, summarized_count
