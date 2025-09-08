import os
import redis
import json
import time
import uuid
import requests
from fastapi import FastAPI
from threading import Thread
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# --- Configuration ---
AGENT_ID = "competitor_agent_v1"
LISTEN_TO_CHANNEL = "entity.found" # Listens for the initial entity
# For the demo, we have a hardcoded list of known competitors
KNOWN_COMPETITORS = ["acme", "omnicorp", "stark industries"]
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-flash-1.5"

app = FastAPI(title=AGENT_ID, version="1.0.0")
redis_client = None

def publish_event(channel, data, trace_id):
    """A helper function to publish a structured event to a Redis channel."""
    if not redis_client: return
    event_envelope = {
        "event_id": str(uuid.uuid4()), "timestamp": time.time(),
        "agent_id": AGENT_ID, "channel": channel, "payload": data,
        "trace_id": trace_id
    }
    redis_client.publish(channel, json.dumps(event_envelope))
    print(f"[{AGENT_ID}] Published to '{channel}'.")

def get_competitive_analysis(competitor_name: str) -> dict:
    """Gets a competitive analysis by calling the OpenRouter LLM API."""
    if not OPENROUTER_API_KEY or "sk-or-..." in OPENROUTER_API_KEY:
        return {"error": "API Key not configured."}
    try:
        prompt = f"""
        You are a competitive intelligence analyst. The user mentioned the competitor '{competitor_name}'.
        Provide a brief, actionable analysis. Return ONLY a valid JSON object with three keys:
        "strengths" (list of strings), "weaknesses" (list of strings), and "counter_strategy" (a short paragraph).
        """
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        return json.loads(response.json()["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"[{AGENT_ID}] LLM call failed: {e}")
        return {"error": "API call failed."}

def process_event(message):
    """Processes an event, checking for known competitor names."""
    try:
        data = json.loads(message["data"])
        trace_id = data.get("trace_id")
        entity = data.get("payload", {}).get("entity", "").lower()
        
        if entity and trace_id and entity in KNOWN_COMPETITORS:
            print(f"[{AGENT_ID}] Known competitor '{entity}' detected. Generating analysis...")
            analysis_data = get_competitive_analysis(entity)
            publish_event("competitor.analysis.generated", analysis_data, trace_id)

    except Exception as e:
        print(f"[{AGENT_ID}] Error processing event: {e}")

def listen_for_events():
    """Connects to Redis and enters a loop to listen for messages."""
    if not redis_client: return
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(LISTEN_TO_CHANNEL)
    print(f"[{AGENT_ID}] Subscribed to '{LISTEN_TO_CHANNEL}'.")
    for message in pubsub.listen():
        process_event(message)

@app.on_event("startup")
async def startup_event():
    """Initializes the Redis connection and starts the listener thread."""
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print(f"[{AGENT_ID}] Successfully connected to Redis.")
        Thread(target=listen_for_events, daemon=True).start()
    except Exception as e:
        print(f"[{AGENT_ID}] CRITICAL: Could not connect to Redis. {e}")
