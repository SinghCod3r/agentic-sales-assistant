import os
import redis
import json
import time
import uuid
import requests
from fastapi import FastAPI
from threading import Thread
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
AGENT_ID = "suggestion_agent_v1"
LISTEN_TO_CHANNEL = "domain.fetched"
# --- OpenRouter API Configuration ---
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# --- Switched to a more stable, free model on OpenRouter ---
MODEL_NAME = "google/gemini-flash-1.5" 


# --- FastAPI App Initialization ---
app = FastAPI(title=AGENT_ID, version="1.0.0")

# --- Redis Connection & Event Publishing ---
redis_client = None

def publish_event(channel, data):
    if not redis_client: return
    event_envelope = {
        "event_id": str(uuid.uuid4()), "timestamp": time.time(),
        "agent_id": AGENT_ID, "channel": channel, "payload": data
    }
    redis_client.publish(channel, json.dumps(event_envelope))
    print(f"[{AGENT_ID}] SUCCESS: Published to '{channel}'.")


def generate_suggestions(context: str) -> list:
    """Generates talking points using the OpenRouter LLM API."""
    if not OPENROUTER_API_KEY or "sk-or-..." in OPENROUTER_API_KEY:
        print(f"[{AGENT_ID}] CRITICAL: OPENROUTER_API_KEY not set correctly in .env file.")
        return ["Mock suggestion: API Key not configured.", "Please check your .env file."]

    try:
        prompt = f"""
        You are a helpful sales assistant. Based on the provided context about a company, generate 3 concise, actionable talking points for a sales representative.
        Return ONLY a valid JSON object with a single key "suggestions" which is a list of strings.
        Company Context: {context}
        """
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:3000", 
            "X-Title": "Live Sales Assistant"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        print(f"[{AGENT_ID}] INFO: Calling OpenRouter API with stable model...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        
        # --- ENHANCED ERROR LOGGING ---
        if response.status_code != 200:
            print(f"[{AGENT_ID}] ERROR: API returned status {response.status_code}. Response: {response.text}")
        response.raise_for_status()

        response_text = response.json()["choices"][0]["message"]["content"]
        suggestions_json = json.loads(response_text)
        print(f"[{AGENT_ID}] INFO: Successfully parsed suggestions from OpenRouter LLM.")
        return suggestions_json.get("suggestions", ["Failed to parse suggestions."])

    except Exception as e:
        print(f"[{AGENT_ID}] CRITICAL: LLM API call failed: {e}.")
        return ["Mock suggestion (API failed).", "Check your API key and network.", "Is OpenRouter down?"]


def process_event(message):
    try:
        data = json.loads(message["data"])
        if data.get("agent_id") == AGENT_ID: return

        if data.get("channel") == LISTEN_TO_CHANNEL:
            description = data.get("payload", {}).get("description", "No context.")
            print(f"[{AGENT_ID}] INFO: Received context. Generating talking points...")
            suggestions = generate_suggestions(description)
            publish_event("suggestions.created", {"suggestions": suggestions, "source_event_id": data.get("event_id")})
    except Exception as e:
        print(f"[{AGENT_ID}] CRITICAL: Error processing event: {e}")

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
        print(f"[{AGENT_ID}] Successfully connected to Redis.")
        thread = Thread(target=listen_for_events, daemon=True)
        thread.start()
    except redis.exceptions.ConnectionError as e:
        print(f"[{AGENT_ID}] CRITICAL: Could not connect to Redis. {e}")

@app.get("/")
def read_root():
    return {"status": "online", "agent_id": AGENT_ID}

