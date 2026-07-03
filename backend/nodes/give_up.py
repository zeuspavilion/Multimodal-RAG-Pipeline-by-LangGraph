from langchain_core.messages import AIMessage

async def give_up_node(state: dict) -> dict:
    answer = "I wasn't able to understand your request after several attempts. Please try again with more detail."
    return {
        "final_answer": answer,
        "messages": [AIMessage(content=answer)]
    }