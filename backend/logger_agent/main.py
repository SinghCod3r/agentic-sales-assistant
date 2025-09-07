import os
import redis
import json
import time
from fastapi import FastAPI
from threading import Thread

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
AGENT_ID = "logger_agent_v1"
LISTEN_TO_CHANNEL = "*" # Wildcard to listen to ALL channels

# --- FastAPI App Initialization ---
app = FastAPI(title=AGENT_ID, version="1.0.0")

# --- Redis Connection & Event Processing ---
redis_client = None

def process_event(message):
    """Processes a single event received from Redis by logging it."""
    try:
        channel = message['channel']
        data = message["data"]
        # For the logger, we just print the raw event to simulate storing it.
        print(f"[{AGENT_ID}] LOG ==> Channel: '{channel}' | Data: {data}")
    except Exception as e:
        print(f"[{AGENT_ID}] CRITICAL: Error processing event: {e}")

def listen_for_events():
    """Connects to Redis and enters a blocking loop to listen for events."""
    if not redis_client: return
    
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.psubscribe(LISTEN_TO_CHANNEL) # Use psubscribe for pattern matching
    
    print(f"[{AGENT_ID}] Subscribed to ALL channels ('{LISTEN_TO_CHANNEL}'). Logging all events...")
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
