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

AGENT_ID = "action_item_agent_v1"
LISTEN_TO_CHANNEL = "summary.created" # Listens for the summary
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-flash-1.5"

app = FastAPI(title=AGENT_ID, version="1.0.0")
redis_client = None

def publish_event(channel, data, trace_id):
    if not redis_client: return
    event_envelope = {
        "event_id": str(uuid.uuid4()), "timestamp": time.time(),
        "agent_id": AGENT_ID, "channel": channel, "payload": data,
        "trace_id": trace_id
    }
    redis_client.publish(channel, json.dumps(event_envelope))
    print(f"[{AGENT_ID}] Published to '{channel}'.")

def generate_action_items(context: str) -> list:
    if not OPENROUTER_API_KEY or "..." in OPENROUTER_API_KEY:
        return ["Mock Action: API Key not configured."]
    try:
        # A new prompt focused on future actions
        prompt = f"""
        You are a proactive sales assistant. Based on the summary of a sales call, generate 2-3 concrete next steps or action items for the sales representative.
        Examples: 'Schedule a follow-up meeting to discuss pricing.', 'Send the case study on Project Titan.', 'Connect with their CTO on LinkedIn.'
        Return ONLY a valid JSON object with a single key "actions" which is a list of strings.
        Context: {context}
        """
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        payload = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        actions = json.loads(response.json()["choices"][0]["message"]["content"]).get("actions", [])
        return actions
    except Exception as e:
        print(f"[{AGENT_ID}] LLM call failed: {e}")
        return ["Mock Action: Send a follow-up email (API Failed)."]

def process_event(message):
    try:
        data = json.loads(message["data"])
        trace_id = data.get("trace_id")
        summary = data.get("payload", {}).get("summary")
        
        if summary and trace_id:
            action_items = generate_action_items(summary)
            publish_event("action_items.created", {"actions": action_items}, trace_id)
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
        Thread(target=listen_for_events, daemon=True).start()
    except Exception as e:
        print(f"[{AGENT_ID}] Startup failed: {e}")
