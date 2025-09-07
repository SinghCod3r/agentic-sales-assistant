import os
import redis
import json
import time
import uuid
from fastapi import FastAPI
from threading import Thread

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
AGENT_ID = "ranking_agent_v1"
LISTEN_TO_CHANNEL = "suggestions.created"

# --- FastAPI App Initialization ---
app = FastAPI(title=AGENT_ID, version="1.0.0")

# --- Redis Connection & Event Publishing ---
redis_client = None

def publish_event(channel, data):
    """Publishes a structured event to a Redis channel."""
    if not redis_client:
        print(f"[{AGENT_ID}] ERROR: Cannot publish event, Redis is not connected.")
        return
    event_envelope = {
        "event_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "agent_id": AGENT_ID,
        "channel": channel,
        "payload": data
    }
    redis_client.publish(channel, json.dumps(event_envelope))
    print(f"[{AGENT_ID}] SUCCESS: Published to '{channel}'.")

def rank_suggestions(suggestions: list) -> list:
    """
    In a real system, this would involve a complex ranking algorithm.
    For the hackathon, we will just pass them through to demonstrate the agent is working.
    """
    print(f"[{AGENT_ID}] INFO: 'Ranking' suggestions (passthrough).")
    return suggestions

def process_event(message):
    """Processes a single event received from Redis."""
    try:
        data = json.loads(message["data"])
        if data.get("agent_id") == AGENT_ID:
            return

        if data.get("channel") == LISTEN_TO_CHANNEL:
            payload = data.get("payload", {})
            suggestions_to_rank = payload.get("suggestions", [])
            
            ranked_suggestions = rank_suggestions(suggestions_to_rank)
            
            publish_event("suggestions.ranked", {"suggestions": ranked_suggestions, "source_event_id": data.get("event_id")})

    except Exception as e:
        print(f"[{AGENT_ID}] CRITICAL: Error processing event: {e}")

def listen_for_events():
    """Connects to Redis and enters a blocking loop to listen for events."""
    if not redis_client: return
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(LISTEN_TO_CHANNEL)
    print(f"[{AGENT_ID}] Subscribed to '{LISTEN_TO_CHANNEL}'. Listening for events...")
    for message in pubsub.listen():
        process_event(message)

@app.on_event("startup")
async def startup_event():
    """Initializes Redis connection and starts the listener thread on app startup."""
    global redis_client
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        redis_client.ping()
        print(f"[{AGENT_ID}] Successfully connected to Redis.")
        thread = Thread(target=listen_for_events, daemon=True)
        thread.start()
    except redis.exceptions.ConnectionError as e:
        print(f"[{AGENT_ID}] CRITICAL: Could not connect to Redis. {e}")
        redis_client = None

@app.get("/")
def read_root():
    return {"status": "online", "agent_id": AGENT_ID}
