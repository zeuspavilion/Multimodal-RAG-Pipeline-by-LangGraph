from langgraph.graph import StateGraph, START, END
from backend.state import AgentState
from backend.nodes.planner import planner_node
from backend.nodes.executor_worker import executor_worker_node
from backend.nodes.url_router import url_router_node, should_process_urls
from backend.nodes.clarification import clarification_node
from backend.nodes.generator import generate_node
from backend.nodes.classify_route import classify_and_route
from backend.nodes.fanout import route_to_workers
from backend.nodes.give_up import give_up_node


builder = StateGraph(AgentState)

builder.add_node("classify_files", classify_and_route)
builder.add_node("planner", planner_node)
builder.add_node("clarification", clarification_node)
builder.add_node("executor_worker", executor_worker_node)
builder.add_node("url_router", url_router_node)
builder.add_node("generate", generate_node)
builder.add_node("give_up", give_up_node)

builder.add_edge(START, "classify_files")
builder.add_edge("classify_files", "planner")

builder.add_conditional_edges("planner", route_to_workers, [
    "clarification",
    "executor_worker",
    "generate",
    "give_up"
])

builder.add_edge("clarification", "planner")

builder.add_conditional_edges("executor_worker", should_process_urls, {
    "url_router": "url_router",
    "generate": "generate"
})

builder.add_edge("url_router", "generate")
builder.add_edge("give_up", END)
builder.add_edge("generate", END)

# compiled without checkpointer — injected at runtime via lifespan
graph_builder = builder

