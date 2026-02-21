"""
LangGraph state machine definition.

Graph:  START → investigator → forensic → synthesizer → END
"""
from langgraph.graph import StateGraph, END

from backend.agents.state import AnalysisState
from backend.agents.nodes import investigator_node, forensic_node, synthesizer_node


def build_graph() -> StateGraph:
    graph = StateGraph(AnalysisState)

    graph.add_node("investigator", investigator_node)
    graph.add_node("forensic", forensic_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.set_entry_point("investigator")
    graph.add_edge("investigator", "forensic")
    graph.add_edge("forensic", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


# Singleton compiled graph
compiled_graph = build_graph()
