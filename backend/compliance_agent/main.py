import os
import redis
import json
import time
import uuid
from fastapi import FastAPI
from threading import Thread

# --- Configuration ---
AGENT_ID = "compliance_agent_v1"
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
        channel = data.get("channel")
        
        # Mock logic: check for events that might contain PII
        if channel == "person.enriched":
            print(f"[{AGENT_ID}] Detected PII in '{channel}'. Running compliance check...")
            time.sleep(0.5) # Simulate check
            publish_event("compliance.checked", {"status": "PASSED", "policy_id": "pii-policy-v2"})

    except Exception as e:
        print(f"[{AGENT_ID}] Error: {e}")

def listen_for_events():
    if not redis_client: return
    pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
    pubsub.psubscribe("*") # Subscribes to ALL channels
    print(f"[{AGENT_ID}] Subscribed to all channels for compliance monitoring.")
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
