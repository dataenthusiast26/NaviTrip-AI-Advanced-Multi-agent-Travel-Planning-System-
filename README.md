# ✈️ NaviTrip AI — Multi-Agent Travel Decision & Planning System

NaviTrip AI is an AI-powered travel decision and planning system that transforms a natural-language travel request into a practical, structured travel plan.

The project uses specialized AI agents coordinated through **LangGraph**, with real-world travel information retrieved through external APIs and web search. The current system combines flight research, hotel research, itinerary generation, and final response synthesis into a single multi-agent workflow.

> 🚧 **Project Status:** Active development. The current version implements the foundational multi-agent workflow. Additional orchestration, validation, and human-in-the-loop capabilities are planned for future iterations.

---

## 🎯 Project Overview

Travel planning often requires switching between multiple platforms to compare flights, research hotels, find accommodation, and create an itinerary.

NaviTrip AI aims to bring these tasks together into one intelligent system.

A user can provide a request such as:

> "Plan a 5-day trip to Goa under ₹50,000."

The system coordinates multiple specialized agents to gather relevant information and generate a practical travel plan.

---

## 🧠 Current Architecture

The current workflow consists of four specialized agents:

```text
                    User Request
                         │
                         ▼
                  ┌──────────────┐
                  │ Flight Agent │
                  └──────┬───────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ Hotel Agent │
                  └──────┬──────┘
                         │
                         ▼
                ┌──────────────────┐
                │ Itinerary Agent  │
                └────────┬─────────┘
                         │
                         ▼
                ┌──────────────────┐
                │  Final Response  │
                │      Agent       │
                └────────┬─────────┘
                         │
                         ▼
                    Travel Plan
```

The agents communicate through a shared **LangGraph state**, allowing information collected by earlier agents to be passed to subsequent agents.

---

## ✨ Current Features

* ✈️ Flight research using the AviationStack API
* 🏨 Hotel research using Tavily web search
* 🧠 Multi-agent orchestration using LangGraph
* 📝 AI-generated day-by-day itineraries
* 💰 Budget-aware travel planning
* 🌐 FastAPI backend
* 🖥️ Responsive web interface
* 💾 PostgreSQL-based LangGraph checkpointing
* 🔗 Persistent workflow threads using `thread_id`
* ⚡ LLM-powered responses using Groq
* 📊 Structured Markdown travel responses
* 📋 Copy generated travel plans directly from the interface

---


## 🔐 Environment Variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
TAVILY_API_KEY=your_tavily_api_key
DATABASE_URL=your_postgresql_connection_string
DEFAULT_ORIGIN_IATA=BOM
```

### Environment Variable Description

| Variable                | Purpose                             |
| ----------------------- | ----------------------------------- |
| `GROQ_API_KEY`          | Authentication for the Groq LLM     |
| `AVIATIONSTACK_API_KEY` | Authentication for AviationStack    |
| `TAVILY_API_KEY`        | Authentication for Tavily search    |
| `DATABASE_URL`          | PostgreSQL connection string        |
| `DEFAULT_ORIGIN_IATA`   | Default departure airport IATA code |

### Security

Never commit your `.env` file or expose API keys publicly.

Make sure `.env` is included in `.gitignore`.

---

## ⚙️ Installation

Make sure Python 3.10+ is installed.

Clone the repository:

```bash
git clone <your-repository-url>
cd "NaviTrip AI"
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Configure your environment variables in `.env`.

---

## ▶️ Running the Application

Start the FastAPI application:

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:8000/
```

Open the URL in your browser to access NaviTrip AI.

---

## 🔌 API Endpoints

### Health Check

```http
GET /health
```

Example response:

```json
{
    "status": "ok",
    "message": "NaviTrip AI API is running"
}
```

---

### Travel Planning

```http
POST /api/travel
```

Example request:

```json
{
    "message": "Plan a 5-day trip to Goa under ₹50,000"
}
```

Example using `curl`:

```bash
curl -X POST http://127.0.0.1:8000/api/travel \
  -H "Content-Type: application/json" \
  -d '{"message":"Plan a 5-day trip to Goa under ₹50,000"}'
```

The API returns the generated travel plan along with the workflow `thread_id` and intermediate agent results.

---

## 🖥️ User Interface

The NaviTrip AI interface allows users to:

* Describe their trip using natural language
* Use example travel prompts
* Submit travel planning requests
* View generated travel plans
* View structured flight and hotel information
* Read day-by-day itineraries
* View Markdown-formatted tables and sections
* Copy the generated travel plan

The interface is designed to present the generated result as a structured travel-planning document rather than a plain chatbot response.

---

## 🚧 Current Limitations

The current implementation is the foundational version of NaviTrip AI.

The following capabilities are planned but are **not yet implemented**:

* Supervisor Agent
* Dynamic agent routing
* Weather Agent
* Activities Agent
* Dedicated Budget Agent
* Critic / validation agent
* Automatic retry and replanning
* Human-in-the-loop approval
* Advanced conversation memory
* RAG-based travel knowledge retrieval
* MCP-based tool integration
* Automated evaluation
* Advanced observability
* Production deployment and hardening

---

## 🤝 Contributing

Contributions and suggestions are welcome.

If you want to contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the application
5. Open a pull request

---

## 📄 License

This project is intended to be open source.

A specific license will be added before the repository is published.
