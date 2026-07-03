from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from backend.state import AgentState
from backend.prompts import GENERATE_SYSTEM_PROMPT
from backend.config import GENERATOR_MODEL
from backend.utils.retry import async_llm_retry
from backend.utils.history import get_recent_history_str

generator_llm = ChatGroq(model=GENERATOR_MODEL)


# ---------------------------------
# Retryable internal call
# ---------------------------------

async def _call_generator(messages: list) -> str:
    """Async generator LLM call with retry."""
    response = await async_llm_retry(generator_llm.ainvoke, messages)
    return response.content


# ---------------------------------
# Node
# ---------------------------------

async def generate_node(state: AgentState):
    # print(f"[generate] task={state['task']}")
    # print(f"[generate] extracted_contents={state['extracted_contents']}")
    
    history_str = get_recent_history_str(state.get("messages", []))
    history_block = f"Conversation History:\n{history_str}\n\n" if history_str else ""
    
    summary = state.get("conversation_summary", "")
    summary_block = f"Earlier in this conversation (Summary):\n{summary}\n\n" if summary else ""
    
    messages = [
        SystemMessage(content=GENERATE_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
            {summary_block}{history_block}User Query:
            {state['query']}

            Task:
            {state['task']}

            Extracted Contents:
            {state['extracted_contents']}

            Note: Any source with "was_summarized": true in the extracted contents JSON was too large for the context
            window and has been pre-summarized. Treat its content as a summary,
            not the full original. Do not reference internal fields (like "was_summarized") in the final response.
            """
        )
    ]

    final_answer = await _call_generator(messages)
    return {
        "final_answer": final_answer,
        "messages": [AIMessage(content=final_answer)]
    }