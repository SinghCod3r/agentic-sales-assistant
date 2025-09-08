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
AGENT_ID = "followup_agent_v1"
LISTEN_TO_CHANNEL = "action_items.created"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-flash-1.5"

app = FastAPI(title=AGENT_ID, version="1.0.0")
redis_client = None

def publish_event(channel, data, trace_id=None):
    if not redis_client: return
    event_envelope = {
        "event_id": str(uuid.uuid4()), "timestamp": time.time(),
        "agent_id": AGENT_ID, "channel": channel, "payload": data,
        "trace_id": trace_id
    }
    redis_client.publish(channel, json.dumps(event_envelope))
    print(f"[{AGENT_ID}] Published to '{channel}'.")

def generate_followup_plan(action_items: list) -> dict:
    """Generates a comprehensive follow-up plan based on action items."""
    if not OPENROUTER_API_KEY or "..." in OPENROUTER_API_KEY:
        return {
            "followup_plan": {
                "immediate_actions": action_items[:2],
                "short_term": action_items[2:4] if len(action_items) > 2 else [],
                "long_term": action_items[4:] if len(action_items) > 4 else []
            },
            "timeline": {
                "next_24_hours": action_items[:1],
                "next_week": action_items[1:3] if len(action_items) > 1 else [],
                "next_month": action_items[3:] if len(action_items) > 3 else []
            },
            "reminders": ["Follow up on proposal", "Check in on demo"],
            "source": "Mock follow-up plan - API key not configured"
        }
    
    try:
        prompt = f"""
        Create a comprehensive follow-up plan based on these action items:
        {json.dumps(action_items, indent=2)}
        
        Return ONLY a valid JSON object with these keys:
        - "followup_plan": object with "immediate_actions", "short_term", "long_term" arrays
        - "timeline": object with "next_24_hours", "next_week", "next_month" arrays
        - "reminders": array of automated reminders to set
        - "priority_levels": object mapping each action to priority (high/medium/low)
        - "success_metrics": array of metrics to track follow-up success
        - "escalation_triggers": array of conditions that should trigger escalation
        
        Focus on creating an actionable, time-bound follow-up strategy.
        """
        
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        followup_data = json.loads(response.json()["choices"][0]["message"]["content"])
        return followup_data
        
    except Exception as e:
        print(f"[{AGENT_ID}] LLM call failed: {e}")
        return {
            "followup_plan": {
                "immediate_actions": action_items[:2],
                "short_term": action_items[2:4] if len(action_items) > 2 else [],
                "long_term": action_items[4:] if len(action_items) > 4 else []
            },
            "timeline": {
                "next_24_hours": action_items[:1],
                "next_week": action_items[1:3] if len(action_items) > 1 else [],
                "next_month": action_items[3:] if len(action_items) > 3 else []
            },
            "reminders": ["Follow up"],
            "source": f"Follow-up plan failed: {str(e)}"
        }

def process_event(message):
    try:
        data = json.loads(message["data"])
        trace_id = data.get("trace_id")
        action_items = data.get("payload", {}).get("actions", [])
        
        if action_items and trace_id:
            print(f"[{AGENT_ID}] Generating follow-up plan...")
            followup_plan = generate_followup_plan(action_items)
            publish_event("followup.plan_generated", followup_plan, trace_id)
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

@app.get("/")
def read_root():
    return {"status": "online", "agent_id": AGENT_ID}
