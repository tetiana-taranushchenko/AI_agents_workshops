"""
Practice Day 1: Building a Coding Agent with LangGraph
=======================================================

Your task: wire up the agent graph.
Tools are in tools.py — implement them first, then come here.

Follow the TODOs below step by step.
"""

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from config import LLM_MODEL
from tools import all_tools

load_dotenv()


# ============================================================
# Step 1: Define the State (done for you)
# ============================================================

class State(TypedDict):
    messages: Annotated[list, add_messages]


# Step 2 = tools.py (you already did it).


# ============================================================
# Step 3: Set up the LLM and the chatbot node
# ============================================================

llm = ChatOpenAI(model=LLM_MODEL)
llm_with_tools = llm.bind_tools(all_tools)


def chatbot(state: State):
    """The main LLM node. Takes current state, returns the AI response."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# ============================================================
# Step 4: Build the graph
# ============================================================

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(all_tools))

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")


# ============================================================
# Step 5: Checkpointer — persistence between calls
# ============================================================

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# When you invoke the graph, pass a config so the checkpointer knows which
# conversation this is:
#     config = {"configurable": {"thread_id": "1"}}
#     graph.invoke({"messages": [...]}, config=config)
