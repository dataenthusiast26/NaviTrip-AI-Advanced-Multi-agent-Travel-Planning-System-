# Used for working with file and folder paths
from pathlib import Path

# Used to print detailed error information
import traceback

# Used to run the FastAPI application
import uvicorn

# FastAPI creates the API; Request accesses incoming HTTP requests
from fastapi import FastAPI, Request

# Used to control HTTP responses and return JSON data
from fastapi.responses import HTMLResponse, JSONResponse

# Serves CSS, JavaScript, and other static files
from fastapi.staticfiles import StaticFiles

# Loads HTML templates from the templates folder
from fastapi.templating import Jinja2Templates

# Validates data received from API requests
from pydantic import BaseModel

# Imports our LangGraph travel workflow
from backend import run_travel_agent


# Gets the absolute path of the project directory
BASE_DIR = Path(__file__).resolve().parent


# Creates the FastAPI application
app = FastAPI(
    title="NaviTrip AI",
    description="Multi-Agent AI Travel Decision and Planning System",
    version="1.0.0"
)


# Makes files inside static/ available to the frontend
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)


# Tells FastAPI where our HTML templates are stored
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


# Defines the structure of a travel API request
class TravelRequest(BaseModel):
    message: str
    thread_id: str | None = None
    
# Handles requests to the home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )
    
# Handles travel planning requests from the frontend
@app.post("/api/travel")
async def travel_planner(request_data: TravelRequest):
    try:
        # Get the user's message and remove extra spaces
        user_message = request_data.message.strip()

        # Reject an empty request
        if not user_message:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Message cannot be empty."
                }
            )

        # Send the user's request to our LangGraph workflow
        result = run_travel_agent(
            user_input=user_message,
            thread_id=request_data.thread_id
        )

        # Send the agent's result back to the frontend
        return JSONResponse(
            content={
                "success": True,
                "thread_id": result["thread_id"],
                "answer": result["answer"],
                "flight_results": result["flight_results"],
                "hotel_results": result["hotel_results"],
                "itinerary": result["itinerary"],
            }
        )

    except Exception as e:
        # Print the error in the terminal for debugging
        print("ERROR:", e)
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

# Handles travel planning requests
@app.post("/api/travel")
async def travel_planner(request_data: TravelRequest):
    try:
        # Get the user's message and remove extra spaces
        user_message = request_data.message.strip()

        # Reject the request if the user didn't provide any message
        if not user_message:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Message cannot be empty."
                }
            )

        # Send the user's request to our LangGraph workflow
        result = run_travel_agent(
            user_input=user_message,
            thread_id=request_data.thread_id
        )

        # Send the travel plan back to the frontend
        return JSONResponse(
            content={
                "success": True,
                "thread_id": result["thread_id"],
                "answer": result["answer"],
                "flight_results": result["flight_results"],
                "hotel_results": result["hotel_results"],
                "itinerary": result["itinerary"],
            }
        )

    except Exception as e:
        # Print the error in the terminal for debugging
        print("ERROR:", e)
        traceback.print_exc()

        # Send the error back to the frontend
        return JSONResponse(
            # 500 Internal Server Error means: The request reached our server, but something went wrong while processing it.
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )
        
# Checks whether the API is running
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "NaviTrip AI API is running"
    }

# Handles requests for the browser tab icon
@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})


# Starts the FastAPI server when this file is run directly
# Only start the server if we directly run app.py
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

        
'''
Frontend
   ↓
POST /api/travel
   ↓
TravelRequest
   ↓
run_travel_agent()
   ↓
LangGraph
   ↓
Flight → Hotel → Itinerary → Final
   ↓
JSONResponse
   ↓
Frontend
'''