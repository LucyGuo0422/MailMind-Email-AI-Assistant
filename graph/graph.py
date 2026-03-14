from langgraph.graph import StateGraph, END
from graph.state import EmailState
from agents.filter_agent import filter_node
from agents.summarize_agent import summarize_node
from interaction.select_node import select_node
from agents.response_agent import response_node
from interaction.review_node import human_review_node
from tools.gmail_sender import save_draft_node


def build_graph():
    g = StateGraph(EmailState)

    g.add_node("filter", filter_node)
    g.add_node("summarize", summarize_node)
    g.add_node("select", select_node)
    g.add_node("generate_reply", response_node)
    g.add_node("human_review", human_review_node)
    g.add_node("save_draft", save_draft_node)

    g.set_entry_point("filter")
    g.add_edge("filter", "summarize")
    g.add_edge("summarize", "select")
    g.add_edge("select", "generate_reply")
    g.add_edge("generate_reply", "human_review")
    g.add_edge("human_review", "save_draft")
    g.add_edge("save_draft", END)

    return g.compile()
