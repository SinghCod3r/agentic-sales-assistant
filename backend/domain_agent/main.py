import os
import redis
import json
import time
import uuid
import random
from fastapi import FastAPI
from threading import Thread

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
AGENT_ID = "domain_intelligence_agent_v1"
LISTEN_TO_CHANNEL = "entity.found"

# --- FastAPI App Initialization (for health checks) ---
app = FastAPI(title=AGENT_ID, version="1.0.0")

# --- Redis Connection & Event Publishing ---
redis_client = None

def publish_event(channel, data):
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

def process_event(message):
    try:
        data = json.loads(message["data"])
        
        # Guard against processing its own messages
        if data.get("agent_id") == AGENT_ID:
            return

        print(f"[{AGENT_ID}] DEBUG: Received event on channel '{data.get('channel')}'.")

        if data.get("channel") == LISTEN_TO_CHANNEL:
            print(f"[{AGENT_ID}] DEBUG: Event matches listening channel.")
            
            entity = data.get("payload", {}).get("entity")
            if entity:
                print(f"[{AGENT_ID}] DEBUG: Extracted entity '{entity}'.")
                
                # Simulate a network call to fetch data
                print(f"[{AGENT_ID}] INFO: Processing entity '{entity}'. Fetching data...")
                time.sleep(2)
                
                fetched_data = {
                    "name": entity,
                    "description": f"Mock description for {entity}, a leading innovator in the tech industry with over {random.randint(100, 100000)} employees.",
                    "source": "Mock API v1.3"
                }
                
                print(f"[{AGENT_ID}] DEBUG: Data fetched. Preparing to publish...")
                publish_event("domain.fetched", fetched_data)
            else:
                print(f"[{AGENT_ID}] WARNING: No entity found in payload.")
    except Exception as e:
        print(f"[{AGENT_ID}] CRITICAL: Error processing event: {e}\nData: {message.get('data', '')}")

def listen_for_events():
    if not redis_client:
        return

    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(LISTEN_TO_CHANNEL)
    print(f"[{AGENT_ID}] Subscribed to '{LISTEN_TO_CHANNEL}'. Listening for events...")
    for message in pubsub.listen():
        process_event(message)

@app.on_event("startup")
async def startup_event():
    global redis_client
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        redis_client.ping()
        print(f"[{AGENT_ID}] Successfully connected to Redis.")
        # Run the listener in a separate thread
        thread = Thread(target=listen_for_events, daemon=True)
        thread.start()
    except redis.exceptions.ConnectionError as e:
        print(f"[{AGENT_ID}] CRITICAL: Could not connect to Redis. {e}")
        redis_client = None

@app.get("/")
def read_root():
    return {"status": "online", "agent_id": AGENT_ID}

