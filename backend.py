import os
from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import ( AnyMessage, HumanMessage, AIMessage, SystemMessage)

import uuid
import psycopg
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver



class TravelState(TypedDict):
    #The operator.add tells LangGraph: When a node returns new messages, 
    # add them to the existing list rather than replacing the list
    messages : Annotated[list[AnyMessage],operator.add]
    user_query : str
    flight_results : list
    hotel_results : str 
    itinerary : str
    
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

from langchain_groq import ChatGroq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing.")

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    api_key=GROQ_API_KEY,
    max_tokens=2200,
)

# =========================
# Flight Agent
# =========================

def flight_agent(state: TravelState):
    query = state["user_query"] # gets the original request from our shared state.
    flight_data = search_flights(query)
    return {
        "flight_results" : flight_data,
        "messages" : [AIMessage(content="Flight results are fetched.")]
    }

# =========================
# Hotel Agent
# =========================

def hotel_agent(state: TravelState):
    query = f"Best hotels for {state['user_query']}"

    hotel_results = tavily_search(query)

    return {
        "hotel_results": hotel_results,
        "messages": [
            AIMessage(content="Hotel information fetched.")
        ]
    }
    
# =========================
# Itinerary Agent
# =========================
# we use the results already stored in state.

def itinerary_agent(state: TravelState):
    user_query = state["user_query"]
    flight_results = state["flight_results"]
    hotel_results = state["hotel_results"]
    # We're giving the LLM the outputs collected by the previous agents.
    # Here's what the other agents found. Now use that information to plan.
    # That's the beginning of actual agent collaboration through shared state.
    prompt = f"""
    Create a practical travel itinerary for the user.

    User Request:
    {user_query}

    Flight Information:
    {flight_results}

    Hotel Information:
    {hotel_results}

    Make the itinerary practical, budget-aware, and easy to follow.
    """
    response = llm.invoke([
        SystemMessage(content="You are an expert travel planner."),
        HumanMessage(content=prompt)
    ])
    
    return {
        "itinerary": response.content,
        "messages": [response]
    }
 
#############################
    
'''

Flight Agent ──→ flight_results ──┐
                                  │
Hotel Agent ───→ hotel_results ───┼──→ Itinerary Agent
                                  │
User ──────────→ user_query ──────┘

'''


# =========================
# Final Response Agent
# =========================

def final_agent(state: TravelState):
    user_query = state["user_query"]
    flight_results = state["flight_results"]
    hotel_results = state["hotel_results"]
    itinerary = state["itinerary"]
    
    prompt = f"""
Generate the final travel response for the user.

User Request:
{user_query}

Flight Information:
{flight_results}

Hotel Information:
{hotel_results}

Itinerary:
{itinerary}

Format the response using these sections:

1. Trip Summary
2. Flight Information
3. Hotel Suggestions
4. Day-by-Day Itinerary
5. Estimated Budget
6. Final Recommendations

Be clear, practical, and useful for real travel planning.
If flight ticket prices are unavailable, clearly mention that.
"""
    response = llm.invoke([
    SystemMessage(content="You are a professional AI travel planning assistant."),
    HumanMessage(content=prompt)
])

    # Gemini may return structured content instead of a plain string
    if isinstance(response.content, list):
        final_answer = "".join(
            item["text"]
            for item in response.content
            if item.get("type") == "text"
        )
    else:
        final_answer = response.content

    return {
        "messages": [AIMessage(content=final_answer)]
    }
    
    

# =========================
# Build Graph
# =========================

graph = StateGraph(TravelState)
graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent", hotel_agent)
graph.add_node("itinerary_agent", itinerary_agent)
graph.add_node("final_agent", final_agent)

graph.add_edge(START, "flight_agent")
graph.add_edge("flight_agent", "hotel_agent")
graph.add_edge("hotel_agent", "itinerary_agent")
graph.add_edge("itinerary_agent", "final_agent")
graph.add_edge("final_agent", END)



# =========================
# PostgreSQL Checkpointer
# =========================

DATABASE_URL = os.getenv("DATABASE_URL")

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True, # database operations are committed automatically.
    row_factory=dict_row # database rows behave like dictionaries rather than tuples.
)
#creates the LangGraph component responsible for saving graph state to PostgreSQL.
checkpointer = PostgresSaver(_conn) 

# sets up the tables/schema that LangGraph needs in the database.
checkpointer.setup()

travel_graph = graph.compile(checkpointer=checkpointer)


# =========================
# Function for FastAPI
# =========================

def run_travel_agent(user_input: str, thread_id: str | None = None):
    if not thread_id:
        # The thread_id identifies a particular conversation/workflow execution.
        # If the caller doesn't provide one, we generate a unique ID.
        thread_id = f"user_{uuid.uuid4().hex}"

    # LangGraph needs to know which checkpoint/thread this execution belongs to.
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": [],
            "hotel_results": "",
            "itinerary": ""
        },
        config=config
    )
    
    content = result["messages"][-1].content

    # Gemini can return text as a list of structured content blocks
    if isinstance(content, list):
        final_answer = "".join(
            item["text"]
            for item in content
            if item.get("type") == "text"
        )
    else:
        final_answer = content
    
    
    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result["flight_results"],
        "hotel_results": result["hotel_results"],
        "itinerary": result["itinerary"],
    }
    
