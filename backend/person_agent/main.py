import os
import redis
import json
import time
import uuid
from fastapi import FastAPI
from threading import Thread

# --- Configuration ---
AGENT_ID = "person_enrichment_agent_v1"
LISTEN_TO_CHANNEL = "entity.found"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

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

def process_event(message):
    try:
        data = json.loads(message["data"])
        entity = data.get("payload", {}).get("entity", "").lower()

        # Simple mock logic: if the entity is a common name, "enrich" it.
        common_names = ["john", "jane", "alex", "samantha"]
        if any(name in entity for name in common_names):
            print(f"[{AGENT_ID}] Person entity '{entity}' detected. Enriching...")
            time.sleep(2) # Simulate API call latency
            
            mock_profile = {
                "name": entity.title(),
                "title": "Senior Director of Innovation",
                "company": data.get("payload", {}).get("entity", "Competitor Inc."),
                "linkedin": f"https://linkedin.com/in/{entity.replace(' ', '')}",
                "source": "Mock People API v2.1"
            }
            publish_event("person.enriched", mock_profile)
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
