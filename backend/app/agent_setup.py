import ast
from typing import Annotated, TypedDict, List, Tuple, Dict, Any, Union
from uuid import uuid4
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages_to_graph
from langgraph.prebuilt import ToolNode, tools_to_graph

# Define a calculator tool
@tool
def calculator(query: str) -> str:
    """A simple calculator tool. Input should be a mathematical expression as a string."""
    try:
        return str(ast.literal_eval(query))
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

# Set up search and tools
search = DuckDuckGoSearchRun()
tools = [search, calculator]

# Create and configure the model with tools
model = ChatOpenAI(temperature=0.1)
model_with_tools = model.bind_tools(tools)

# Define the agent state
class AgentState(TypedDict):
    messages: List[Union[HumanMessage, AIMessage]]
    next: str

# Create the graph
def create_agent_graph() -> StateGraph:
    # Create nodes
    model_node = ToolNode(model_with_tools)
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add model node to graph
    workflow.add_node("agent", model_node)
    
    # Create edges
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", "agent")
    
    # Add conditional edges
    workflow.set_finish_point("agent")
    
    return workflow

# Function to run the agent
async def run_agent(query: str) -> List[Dict[str, Any]]:
    # Initialize the graph
    graph = create_agent_graph()
    
    # Create initial state
    state = AgentState(
        messages=[HumanMessage(content=query)],
        next="agent"
    )
    
    # Run the graph
    result = await graph.arun(state)
    
    return result["messages"] 