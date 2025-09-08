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
AGENT_ID = "meeting_notes_agent_v1"
LISTEN_TO_CHANNEL = "summary.created"
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

def structure_meeting_notes(summary: str) -> dict:
    """Structures meeting notes from the conversation summary."""
    if not OPENROUTER_API_KEY or "..." in OPENROUTER_API_KEY:
        return {
            "meeting_notes": {
                "attendees": ["Sales Rep", "Prospect"],
                "key_topics": ["Product discussion", "Pricing"],
                "decisions_made": ["Follow-up scheduled"],
                "next_meeting": "TBD"
            },
            "action_items": ["Send proposal", "Schedule demo"],
            "key_quotes": ["Customer showed interest in our solution"],
            "source": "Mock meeting notes - API key not configured"
        }
    
    try:
        prompt = f"""
        Structure this sales conversation summary into organized meeting notes:
        {summary}
        
        Return ONLY a valid JSON object with these keys:
        - "meeting_notes": object with "attendees", "key_topics", "decisions_made", "next_meeting"
        - "action_items": array of specific action items
        - "key_quotes": array of important quotes from the conversation
        - "pain_points": array of customer pain points mentioned
        - "budget_indicators": array of budget-related information
        - "timeline": estimated timeline for decision making
        
        Focus on extracting actionable information for follow-up.
        """
        
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        notes_data = json.loads(response.json()["choices"][0]["message"]["content"])
        return notes_data
        
    except Exception as e:
        print(f"[{AGENT_ID}] LLM call failed: {e}")
        return {
            "meeting_notes": {
                "attendees": ["Unknown"],
                "key_topics": ["General discussion"],
                "decisions_made": ["None"],
                "next_meeting": "TBD"
            },
            "action_items": ["Follow up"],
            "key_quotes": ["No quotes extracted"],
            "source": f"Meeting notes failed: {str(e)}"
        }

def process_event(message):
    try:
        data = json.loads(message["data"])
        trace_id = data.get("trace_id")
        summary = data.get("payload", {}).get("summary")
        
        if summary and trace_id:
            print(f"[{AGENT_ID}] Structuring meeting notes...")
            meeting_notes = structure_meeting_notes(summary)
            publish_event("meeting.notes_structured", meeting_notes, trace_id)
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
