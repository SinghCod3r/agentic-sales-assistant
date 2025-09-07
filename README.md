# Agentic Live Sales Assistant

This is a multi-agent AI system built for the Oosc3.0 hackathon. It provides real-time talking points, action items, and summaries to a sales representative during a live meeting, with a focus on transparency and provenance.

## Features

- **Multi-Agent Architecture:** A system of 11 independent microservices collaborating via a Redis event bus.
- **Real-Time Intelligence:** Generates talking points, action items, and a final summary using a Large Language Model (LLM).
- **Transparent UI:** A professional, dark-themed dashboard that visualizes the agent workflow in real-time with a live event log and progress bar.
- **Provenance & Auditability:** A dedicated Logger agent captures every event for a complete audit trail.
- **Built for Resilience:** Gracefully handles API failures with a fallback system.

## Tech Stack

- **Backend:** Python, FastAPI, Redis
- **Frontend:** React.js
- **AI:** OpenRouter API (Nous Hermes 2 Mixtral & Google Gemini Pro)
- **Communication:** Server-Sent Events (SSE)

## How to Run Locally

1. Ensure you have Python, Node.js, and Redis installed and running.
2. Clone the repository.
3. For each agent in the `backend/` directory, run `pip install -r requirements.txt`.
4. Create a `.env` file in `backend/suggestion_agent`, `backend/summarizer_agent`, and `backend/action_item_agent` with your `OPENROUTER_API_KEY`.
5. Start each of the 11 backend agents in a separate terminal using `uvicorn main:app --reload`.
6. In a separate terminal, navigate to `frontend/` and run `npm start`.