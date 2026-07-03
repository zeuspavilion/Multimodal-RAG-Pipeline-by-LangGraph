from backend.state import AgentState
from langgraph.types import interrupt
from langchain_core.messages import HumanMessage


async def clarification_node(state: AgentState):
    user_response = interrupt({
        "question": state["clarification_question"]
    })

    return {
        "query": user_response,
        "awaiting_clarification": False,
        "clarification_attempts": state.get("clarification_attempts", 0) + 1,
        "messages": [HumanMessage(content=user_response)]
    }