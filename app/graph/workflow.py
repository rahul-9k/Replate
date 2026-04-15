# app/graph/workflow.py

from langgraph.graph import StateGraph, END

from app.graph.state import AgentState

# Agents
from app.agents.monitoring import monitoring_agent
from app.agents.ngo_fetcher import ngo_fetcher_agent
from app.agents.prediction import prediction_agent
from app.agents.matching import matching_agent
from app.agents.planning import planning_agent
from app.agents.action import action_agent


def build_graph():
    """
    Build LangGraph workflow for Food Redistribution System.
    """

    builder = StateGraph(AgentState)

    # -------------------------
    # Add nodes
    # -------------------------
    builder.add_node("monitor", monitoring_agent)
    builder.add_node("fetch_ngos", ngo_fetcher_agent)
    builder.add_node("predict", prediction_agent)
    builder.add_node("match", matching_agent)
    builder.add_node("plan", planning_agent)
    builder.add_node("act", action_agent)

    # -------------------------
    # Define flow
    # -------------------------
    builder.set_entry_point("monitor")

    builder.add_edge("monitor", "fetch_ngos")
    builder.add_edge("fetch_ngos", "predict")
    builder.add_edge("predict", "match")
    builder.add_edge("match", "plan")
    builder.add_edge("plan", "act")

    builder.add_edge("act", END)

    # -------------------------
    # Compile
    # -------------------------
    return builder.compile()