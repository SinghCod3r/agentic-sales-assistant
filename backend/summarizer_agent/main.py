import os
import redis
import threading
import json
from fastapi import FastAPI
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

# --- FastAPI App ---
app = FastAPI()

# --- Redis Connection ---
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    print("✅ Summarizer Agent connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"❌ Summarizer Agent could not connect to Redis: {e}")
    redis_client = None

# --- OpenAI Client for OpenRouter ---
if not OPENROUTER_API_KEY:
    print("⚠️ Summarizer Agent: OPENROUTER_API_KEY not found in .env file.")
    llm_client = None
else:
    llm_client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_API_BASE,
    )
    print("✅ Summarizer Agent: OpenAI client for OpenRouter configured.")

def generate_summary(context: str) -> str:
    """Calls the LLM to generate a summary from the given context."""
    if not llm_client:
        print("❌ LLM client not configured. Cannot generate summary.")
        return "Summary could not be generated due to configuration error."

    print("🧠 Generating summary from context...")
    try:
        response = llm_client.chat.completions.create(
            model="nousresearch/nous-hermes-2-mixtral-8x7b-dpo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Summarize the following context in one concise paragraph for a sales executive."},
                {"role": "user", "content": context}
            ],
            temperature=0.5,
            max_tokens=200
        )
        summary = response.choices[0].message.content.strip()
        print("👍 Summary generated successfully.")
        return summary
    except Exception as e:
        print(f"❌ Error during summary generation API call: {e}")
        return "Summary could not be generated due to an API error."

def summarizer_task():
    """A background task that listens for retrieved data and creates a summary."""
    if not redis_client:
        return

    pubsub = redis_client.pubsub()
    # This agent should listen for when the retriever has finished its job
    pubsub.subscribe("retriever.completed")
    print("👂 Summarizer listening for 'retriever.completed' event...")

    for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            snippets = data.get("retrieved_snippets")
            
            if snippets and isinstance(snippets, list):
                print("📩 Received retrieved snippets. Starting summarization.")
                context_to_summarize = "\n".join(snippets)
                
                summary_text = generate_summary(context_to_summarize)
                
                # THIS IS THE CRITICAL PART: Create the correct payload
                payload = {"summary": summary_text}
                
                redis_client.publish("summary.created", json.dumps(payload))
                print("📣 Published 'summary.created' event with summary.")
            else:
                print("⚠️ Received 'retriever.completed' message but no snippets found.")

@app.on_event("startup")
async def startup_event():
    print("🚀 Summarizer Agent starting up...")
    thread = threading.Thread(target=summarizer_task, daemon=True)
    thread.start()