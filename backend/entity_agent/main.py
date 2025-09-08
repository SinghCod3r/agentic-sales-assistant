import os
import redis
import json
import time
import uuid
from fastapi import FastAPI
from threading import Thread

# --- Configuration ---
AGENT_ID = "entity_extraction_agent_v1"
LISTEN_TO_CHANNEL = "transcript.new"
# This will default to your local Redis instance but use the cloud URL when deployed
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# --- FastAPI App Initialization ---
# This line is essential for the `uvicorn` command to start the server.
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

def process_event(message):
    """Processes an event by 'extracting' the entity from the raw text."""
    try:
        data = json.loads(message["data"])
        trace_id = data.get("trace_id")
        raw_text = data.get("payload", {}).get("text")
        
        if raw_text and trace_id:
            # In a real system, this is where NLP would happen.
            # For the demo, we assume the whole text is the key entity.
            print(f"[{AGENT_ID}] Extracted entity: '{raw_text}'")
            publish_event("entity.found", {"entity": raw_text}, trace_id)

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
        # Ensures the connection is secure (SSL/TLS) for cloud providers like Upstash
        final_url = REDIS_URL
        if "upstash.io" in REDIS_URL and not REDIS_URL.startswith("rediss://"):
            final_url = "rediss://" + REDIS_URL.split("://")[-1]
        
        redis_client = redis.from_url(final_url, decode_responses=True)
        redis_client.ping()
        print(f"[{AGENT_ID}] Successfully connected to Redis.")
        
        Thread(target=listen_for_events, daemon=True).start()
    except Exception as e:
        print(f"[{AGENT_ID}] CRITICAL: Could not connect to Redis. {e}")