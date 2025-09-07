import os
import redis
import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time
import uuid
from fastapi.middleware.cors import CORSMiddleware

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
AGENT_ID = "ui_agent_v1"

# --- FastAPI App Initialization ---
app = FastAPI(title="UI Agent Service (SSE)", version="2.0.0")

# --- CORS MIDDLEWARE (No changes needed here) ---
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    print(f"[{AGENT_ID}] Published to '{channel}': {data}")

@app.on_event("startup")
async def startup_event():
    global redis_client
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        redis_client.ping()
        print(f"[{AGENT_ID}] Successfully connected to Redis.")
    except redis.exceptions.ConnectionError as e:
        print(f"[{AGENT_ID}] CRITICAL: Could not connect to Redis. {e}")
        redis_client = None

# --- SSE Streaming Endpoint ---
@app.get("/stream")
async def stream_events(request: Request):
    async def event_generator():
        if not redis_client:
            yield f"data: {json.dumps({'agent_id': 'System', 'payload': {'error': 'Redis not connected'}})}\n\n"
            return

        pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
        pubsub.psubscribe("*")
        print(f"[{AGENT_ID}] Client connected to SSE stream.")
        
        # Send a connection confirmation message
        yield f"data: {json.dumps({'agent_id': 'System', 'payload': {'message': 'SSE Connection Established!'}})}\n\n"

        while True:
            # Check if the client has disconnected
            if await request.is_disconnected():
                print(f"[{AGENT_ID}] Client disconnected from SSE stream.")
                break
            
            message = pubsub.get_message()
            if message:
                print(f"[{AGENT_ID}] Relaying event: {message['data']}")
                yield f"data: {message['data']}\n\n"
            
            await asyncio.sleep(0.01) # Non-blocking sleep

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- Trigger Endpoint (No changes needed here) ---
class TriggerPayload(BaseModel):
    text: str

@app.post("/trigger")
async def trigger_workflow(payload: TriggerPayload):
    print(f"[{AGENT_ID}] Received trigger with text: '{payload.text}'")
    publish_event("entity.found", {"entity": payload.text})
    return {"status": "workflow triggered", "entity": payload.text}

@app.get("/")
def read_root():
    return {"status": "online", "agent_id": AGENT_ID}

