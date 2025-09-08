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
    print("✅ Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"❌ Could not connect to Redis: {e}")
    redis_client = None

# --- OpenAI Client for OpenRouter ---
if not OPENROUTER_API_KEY:
    print("⚠️ OPENROUTER_API_KEY not found in .env file.")
    llm_client = None
else:
    llm_client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_API_BASE,
    )
    print("✅ OpenAI client for OpenRouter configured.")

def perform_sentiment_analysis(summary_text: str) -> str:
    """Calls the LLM to get the sentiment of the text."""
    if not llm_client:
        print("❌ LLM client not configured. Cannot perform analysis.")
        return "NEUTRAL"
        
    print(f"🧠 Performing sentiment analysis on summary...")
    try:
        response = llm_client.chat.completions.create(
            model="nousresearch/nous-hermes-2-mixtral-8x7b-dpo",
            messages=[
                {"role": "system", "content": "You are a sentiment analysis expert. Analyze the given text and respond with only one word: POSITIVE, NEGATIVE, or NEUTRAL."},
                {"role": "user", "content": summary_text}
            ],
            temperature=0.1,
            max_tokens=5
        )
        sentiment = response.choices[0].message.content.strip().upper()
        print(f"👍 Sentiment analysis successful. Result: {sentiment}")
        return sentiment
    except Exception as e:
        print(f"❌ Error during sentiment analysis API call: {e}")
        return "NEUTRAL" # Fallback sentiment

def sentiment_analysis_task():
    """A background task that listens for summaries and performs sentiment analysis."""
    if not redis_client:
        print("❌ Redis client not available. Cannot start sentiment analysis task.")
        return

    pubsub = redis_client.pubsub()
    pubsub.subscribe("summary.created")
    print("👂 Listening for 'summary.created' event...")

    for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            summary = data.get("summary")
            
            if summary:
                print("📩 Received summary. Starting sentiment analysis.")
                sentiment = perform_sentiment_analysis(summary)
                
                # Publish the result
                result = {"sentiment": sentiment, "source_summary": summary}
                redis_client.publish("sentiment.completed", json.dumps(result))
                print("📣 Published 'sentiment.completed' event.")
            else:
                print("⚠️ Received message on 'summary.created' but no summary text found.")


@app.on_event("startup")
async def startup_event():
    """Start the background thread when the app starts."""
    print("🚀 Sentiment Agent starting up...")
    thread = threading.Thread(target=sentiment_analysis_task, daemon=True)
    thread.start()