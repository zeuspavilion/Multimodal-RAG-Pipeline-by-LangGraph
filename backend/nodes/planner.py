from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from backend.state import AgentState, PlannerDecision
from backend.prompts import PLANNER_SYSTEM_PROMPT
from backend.config import PLANNER_MODEL
from backend.utils.retry import async_llm_retry
from backend.utils.history import get_recent_history_str, update_conversation_summary_if_needed

llm = ChatGroq(model=PLANNER_MODEL)
planner_llm = llm.with_structured_output(PlannerDecision, method="json_mode")

MAX_CLARIFICATION_ATTEMPTS = 3


# ---------------------------------
# Retryable internal call
# ---------------------------------

async def _call_planner(messages: list) -> PlannerDecision:
    """Async planner LLM call with retry."""
    return await async_llm_retry(planner_llm.ainvoke, messages)


# ---------------------------------
# Node
# ---------------------------------

async def planner_node(state: AgentState):
    print(f"[planner_node] Current thread messages count: {len(state.get('messages', []))}")

    # Incrementally update conversation summary
    summary, count = await update_conversation_summary_if_needed(
        messages=state.get("messages", []),
        existing_summary=state.get("conversation_summary", ""),
        summarized_count=state.get("summarized_message_count", 0)
    )

    history_str = get_recent_history_str(state.get("messages", []))
    history_block = f"Conversation History:\n{history_str}\n\n" if history_str else ""
    summary_block = f"Earlier in this conversation (Summary):\n{summary}\n\n" if summary else ""

    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""
            {summary_block}{history_block}User Query:
            {state["query"]}

            Available PDF Files:
            {state["pdf_files"]}

            Available Audio Files:
            {state["audio_files"]}

            Available Image Files:
            {state["image_files"]}
            """
        )
    ]

    decision = await _call_planner(messages)

    ret = {
        "query": state["query"],
        "task": decision.task,
        "required_actions": [
            {**action.model_dump(), "action_id": action.action_id or f"action_{i+1}"}
            for i, action in enumerate(decision.required_actions)
        ],
        "needs_clarification": decision.needs_clarification,
        "clarification_question": decision.clarification_question,
        "conversation_summary": summary,
        "summarized_message_count": count
    }

    if decision.needs_clarification and decision.clarification_question:
        ret["messages"] = [AIMessage(content=decision.clarification_question)]

    return ret