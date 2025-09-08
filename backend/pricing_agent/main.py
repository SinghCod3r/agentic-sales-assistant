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
AGENT_ID = "pricing_intelligence_agent_v1"
LISTEN_TO_CHANNEL = "competitor.analyzed"
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

def generate_pricing_strategy(competitor_data: dict) -> dict:
    """Generates pricing strategy based on competitor analysis."""
    if not OPENROUTER_API_KEY or "..." in OPENROUTER_API_KEY:
        return {
            "pricing_strategy": {
                "recommended_approach": "Value-based pricing",
                "price_range": "$50,000 - $75,000",
                "discount_strategy": "10-15% for annual contracts"
            },
            "competitive_advantages": ["Superior support", "Better integration"],
            "pricing_tactics": ["Bundle services", "Offer pilot programs"],
            "source": "Mock pricing strategy - API key not configured"
        }
    
    try:
        prompt = f"""
        Based on this competitor analysis, generate a pricing strategy for our sales team:
        {json.dumps(competitor_data, indent=2)}
        
        Return ONLY a valid JSON object with these keys:
        - "pricing_strategy": object with "recommended_approach", "price_range", "discount_strategy"
        - "competitive_advantages": array of our advantages to highlight
        - "pricing_tactics": array of specific pricing tactics to use
        - "value_proposition": string describing our unique value
        - "negotiation_tips": array of tips for price negotiations
        
        Focus on actionable pricing insights for sales conversations.
        """
        
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        payload = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        pricing_data = json.loads(response.json()["choices"][0]["message"]["content"])
        return pricing_data
        
    except Exception as e:
        print(f"[{AGENT_ID}] LLM call failed: {e}")
        return {
            "pricing_strategy": {
                "recommended_approach": "Competitive pricing",
                "price_range": "Market rate",
                "discount_strategy": "Standard discounts"
            },
            "competitive_advantages": ["Quality", "Service"],
            "pricing_tactics": ["Focus on value"],
            "source": f"Pricing analysis failed: {str(e)}"
        }

def process_event(message):
    try:
        data = json.loads(message["data"])
        trace_id = data.get("trace_id")
        competitor_data = data.get("payload", {})
        
        if competitor_data and trace_id:
            print(f"[{AGENT_ID}] Generating pricing strategy...")
            pricing_strategy = generate_pricing_strategy(competitor_data)
            publish_event("pricing.strategy_generated", pricing_strategy, trace_id)
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
