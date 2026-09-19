import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage
)

import uuid
import psycopg
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver


class TravelState(TypedDict):
    #The operator.add tells LangGraph: When a node returns new messages, 
    # add them to the existing list rather than replacing the list
    messages: Annotated[list[AnyMessage], operator.add]

    user_query: str

    flight_results: list

    hotel_results: str

    weather_results: str

    itinerary: str
    
    budget: str


# ==========================================
# MCP Tools
# ==========================================

from mcp_client import (
    tavily_mcp_search,
    aviation_mcp_call,
    weather_mcp_search,
    forecast_mcp_search,
    extract_destination,
)


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
# Flight Agent Prompt
# =========================

FLIGHT_AGENT_PROMPT = """
You are a travel flight expert.

User Query:
{query}

Airport Information:
{airport_data}

Airline Information:
{airline_data}

Generate:

1. Likely departure airport
2. Likely arrival airport
3. Airlines serving this route
4. Typical flight duration
5. Estimated airfare range
6. Peak season pricing warning
7. Booking advice

Return concise travel guidance.
"""


# =========================
# Flight Agent
# =========================

def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    query = state["user_query"]

    try:

        airports = asyncio.run(
            aviation_mcp_call(
                "list_airports"
            )
        )

        airlines = asyncio.run(
            aviation_mcp_call("list_airlines")
        )
        

        print("\nAIRPORTS:", airports)
        print("\nAIRLINES:", airlines)

        prompt = FLIGHT_AGENT_PROMPT.format(
            query=query,
            airport_data=str(airports)[:3000],
            airline_data=str(airlines)[:3000]
        )

        response = llm.invoke([
            SystemMessage(
                content="You are an expert travel flight planner."
            ),
            HumanMessage(
                content=prompt
            )
        ])

        flight_data = response.content

    except Exception as e:

        print(
            f"FLIGHT AGENT ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True
        )

        flight_data = (
            f"Flight information unavailable: {str(e)}"
        )

    return {
        "flight_results": flight_data,

        "messages": [
            AIMessage(
                content="Flight recommendations generated"
            )
        ]
    }
    

# =========================
# Hotel Agent
# =========================

def hotel_agent(state: TravelState):
    """
    Search for hotels using Tavily MCP.
    """

    query = (
        f"Best hotels for "
        f"{state['user_query']}"
    )

    try:

        hotel_results = asyncio.run(
            tavily_mcp_search(query)
        )
        

    except Exception as exc:

        print(
            f"HOTEL AGENT MCP ERROR: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        hotel_results = (
            "Hotel information is "
            "temporarily unavailable."
        )

    return {
        "hotel_results": hotel_results,

        "messages": [
            AIMessage(
                content="Hotel information fetched."
            )
        ]
    }


# =========================
# Weather Agent
# =========================

def weather_agent(state: TravelState):
    """
    Get current weather and forecast for the
    destination using the Weather MCP server.
    """

    city = extract_destination(
        state["user_query"]
    )

    try:

        # Current weather
        weather_data = asyncio.run(
            weather_mcp_search(city)
        )
        

        # Forecast
        forecast_data = asyncio.run(
            forecast_mcp_search(city)
        )
        

        weather_results = f"""
Current Weather:
{weather_data}

Forecast:
{forecast_data}
"""

    except Exception as exc:

        print(
            f"WEATHER AGENT MCP ERROR: "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )

        weather_results = (
            f"Live weather information for "
            f"{city} is temporarily unavailable. "
            "Please verify the weather forecast "
            "before departure."
        )

    return {
        "weather_results": weather_results,

        "messages": [
            AIMessage(
                content="Weather information fetched."
            )
        ],
    }


# =========================
# Itinerary Agent
# =========================
# we use the results already stored in state.

def itinerary_agent(state: TravelState):

    user_query = state["user_query"]

    flight_results = state["flight_results"]

    hotel_results = state["hotel_results"]

    weather_results = state["weather_results"]

    # We're giving the LLM the outputs collected
    # by the previous agents.
    #
    # Here's what the other agents found.
    # Now use that information to plan.
    #
    # This is agent collaboration through
    # shared LangGraph state.

    prompt = f"""
    Create a practical travel itinerary for the user.

    User Request:
    {user_query}

    Flight Information:
    {flight_results}

    Hotel Information:
    {hotel_results}

    Weather Information:
    {weather_results}

    Make the itinerary practical,
budget-aware, and easy to follow.

Use INR (₹) for all costs and budget estimates.
Do not convert the budget into USD or another currency.

Consider the weather when suggesting
activities and planning the trip.
    """

    response = llm.invoke([
        SystemMessage(
            content="You are an expert travel planner."
        ),
        HumanMessage(
            content=prompt
        )
    ])

    return {
        "itinerary": response.content,

        "messages": [
            response
        ]
    }

def budget_agent(state: TravelState):
    """
    Creates a simple budget estimate from the
    available travel information.
    """

    prompt = f"""
    Estimate the travel budget from the information below.

    User Request:
    {state["user_query"]}

    Flight Information:
    {state["flight_results"]}

    Hotel Information:
    {state["hotel_results"]}

    Create a concise budget estimate.

    Rules:
    - Use INR (₹).
    - Clearly label estimates.
    - Do not invent exact prices when unavailable.
    - Use a reasonable range when exact prices are unavailable.
    - Include:
      Flights
      Hotel
      Food
      Local Transport
      Activities
      Total Estimated Budget
    """

    response = llm.invoke([
        SystemMessage(
            content="You are a practical travel budget estimator."
        ),
        HumanMessage(content=prompt)
    ])

    return {
        "budget": response.content,
        "messages": [
            AIMessage(content="Travel budget estimated.")
        ]
    }
    
    
#############################

'''
Flight Agent ──→ flight_results ──┐
                                  │
Hotel Agent ───→ hotel_results ───┤
                                  │
Weather Agent → weather_results ──┼──→ Itinerary Agent
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

    weather_results = state["weather_results"]

    itinerary = state["itinerary"]
    
    budget = state["budget"]

    prompt = f"""
Generate a concise travel plan.

User Request:
{user_query}

Flight Information:
{flight_results}

Hotel Information:
{hotel_results}

Weather Information:
{weather_results}

Itinerary:
{itinerary}

Budget Information:
{budget}

Use these sections:

1. Trip Summary
2. Flight Information
3. Hotel Suggestions
4. Weather Information
5. Day-by-Day Itinerary
6. Estimated Budget
7. Final Recommendations

Rules:
- Use INR (₹) for all monetary values.
- Do not use USD or other currencies unless the user asks.
- Keep each section concise.
- Use tables or bullet points where useful.
- Avoid long explanations.
- Do not repeat information.
- Give only the most useful recommendations.
- Keep the complete response under approximately 1200 words.
- If exact flight prices are unavailable, clearly say so.
"""

    response = llm.invoke([
        SystemMessage(
            content=(
                "You are a professional AI "
                "travel planning assistant."
            )
        ),
        HumanMessage(
            content=prompt
        )
    ])

    # Gemini may return structured content
    # instead of a plain string.
    if isinstance(response.content, list):

        final_answer = "".join(
            item["text"]
            for item in response.content
            if item.get("type") == "text"
        )

    else:

        final_answer = response.content

    return {
        "messages": [
            AIMessage(
                content=final_answer
            )
        ]
    }


# =========================
# Build Graph
# =========================

graph = StateGraph(TravelState)

graph.add_node( "flight_agent", flight_agent )

graph.add_node("hotel_agent",hotel_agent )

graph.add_node( "weather_agent", weather_agent )

graph.add_node( "itinerary_agent", itinerary_agent )

graph.add_node("budget_agent", budget_agent)

graph.add_node( "final_agent", final_agent )


graph.add_edge( START, "flight_agent" )

graph.add_edge( "flight_agent", "hotel_agent" )

graph.add_edge( "hotel_agent", "weather_agent" )

graph.add_edge("weather_agent", "itinerary_agent")

graph.add_edge("itinerary_agent", "budget_agent")

graph.add_edge("budget_agent", "final_agent")

graph.add_edge( "final_agent", END )


# =========================
# PostgreSQL Checkpointer
# =========================

DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row
)

# Creates the LangGraph component responsible
# for saving graph state to PostgreSQL.
checkpointer = PostgresSaver(
    _conn
)

# Sets up the tables/schema that LangGraph needs.
checkpointer.setup()

travel_graph = graph.compile(
    checkpointer=checkpointer
)


# =========================
# Function for FastAPI
# =========================

def run_travel_agent(
    user_input: str,
    thread_id: str | None = None
):

    if not thread_id:

        # The thread_id identifies a particular
        # conversation/workflow execution.
        thread_id = (
            f"user_{uuid.uuid4().hex}"
        )

    # LangGraph needs to know which checkpoint
    # this execution belongs to.

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content=user_input
                )
            ],

            "user_query": user_input,

            "flight_results": [],

            "hotel_results": "",

            "weather_results": "",

            "itinerary": "",
            
            "budget": ""
        },

        config=config
    )

    content = (
        result["messages"][-1].content
    )

    # Gemini can return text as a list of
    # structured content blocks.
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

        "flight_results": (
            result["flight_results"]
        ),

        "hotel_results": (
            result["hotel_results"]
        ),

        "weather_results": (
            result["weather_results"]
        ),

        "itinerary": (
            result["itinerary"]
        ),
        
        "budget": (
        result["budget"]
        ),
    }