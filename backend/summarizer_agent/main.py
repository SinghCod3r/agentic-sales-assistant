import os
import redis
import json
import time
import uuid
import requests
from fastapi import FastAPI
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
AGENT_ID = "summarizer_agent_v1"
LISTEN_TO_CHANNEL = "documents.retrieved"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-flash-1.5"

app = FastAPI(title=AGENT_ID, version="1.0.0")
redis_client = None

def publish_event(channel, data):
    if not redis_client: return
    event_envelope = {
        "event_id": str(uuid.uuid4()), "timestamp": time.time(),
        "agent_id": AGENT_ID, "channel": channel, "payload": data
    }
    redis_client.publish(channel, json.dumps(event_envelope))
    print(f"[{AGENT_ID}] Published to '{channel}'.")

def summarize_text(snippets: list) -> str:
    if not OPENROUTER_API_KEY or "sk-or-..." in OPENROUTER_API_KEY:
        return "Mock summary: API Key not configured."
    try:
        context = "\n".join(snippets)
        prompt = f"Summarize the key insights from the following internal documents into a single, concise paragraph for a sales executive. Context:\n{context}"
        
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        print(f"[{AGENT_ID}] Calling OpenRouter to summarize...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        summary = response.json()["choices"][0]["message"]["content"]
        print(f"[{AGENT_ID}] Summary generated successfully.")
        return summary
    except Exception as e:
        print(f"[{AGENT_ID}] LLM call failed: {e}")
        return "Mock summary (API Failed)."

def process_event(message):
    try:
        data = json.loads(message["data"])
        snippets = data.get("payload", {}).get("retrieved_snippets", [])
        if not snippets: return

        summary = summarize_text(snippets)
        publish_event("summary.created", {"summary": summary})
    except Exception as e:
        print(f"[{AGENT_ID}] Error: {e}")

def listen_for_events():
    if not redis_client: return
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(LISTEN_TO_CHANNEL)
    print(f"[{AGENT_ID}] Subscribed to '{LISTEN_TO_CHANNEL}'.")
    for message in pubsub.listen():
        process_event(message)

@app.on_event("startup")
async def startup_event():
    global redis_client
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        redis_client.ping()
        print(f"[{AGENT_ID}] Connected to Redis.")
        thread = Thread(target=listen_for_events, daemon=True)
        thread.start()
    except redis.exceptions.ConnectionError as e:
        print(f"[{AGENT_ID}] Redis connection failed: {e}")

@app.get("/")
def read_root():
    return {"status": "online", "agent_id": AGENT_ID}
