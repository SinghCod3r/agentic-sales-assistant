# Agentic Live Sales Assistant

This is a multi-agent AI system built for the Oosc3.0 hackathon. It provides real-time talking points, action items, and summaries to a sales representative during a live meeting, with a focus on transparency and provenance.

## Features

- **Multi-Agent Architecture:** A system of 17 independent microservices collaborating via a Redis event bus.
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
4. Create a `.env` file in each agent directory that requires it with your `OPENROUTER_API_KEY`.
5. Start all agents using the provided `start_agents.py` script, or start each of the 17 backend agents manually using `uvicorn main:app --reload`.
6. In a separate terminal, navigate to `frontend/` and run `npm start`.

## Team Members - Who Made This Agent to works better 

- **Member-1 Name:** Ayush Singh (Backend Developer, Domain Expertise)
- **Member-1 Email-ID:** ayushsinghceee@gmail.com
- **Member-2 Name:** Lucky Tiwari (Front-End Developer)
- **Member-2 Email-ID:** luckytiwari.stnt@gmail.com
- **Member-3 Name:** Saksham Tiwari (Documentation)
- **Member-3 Email-ID:** 1234.sakshamtiwari@gmail.com
- **Member-4 Name:** Satyam Shukla (Testing)
- **Member-4 Email-ID:** er.satyamshukla7@gmail.com
- **Member-5 Name:** Aman Mishra (Project Manager)
- **Member-5 Email-ID:** amanmishra.stnt@gmail.com
