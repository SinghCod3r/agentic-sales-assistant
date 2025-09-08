import os

# A list of all your agent directories
AGENTS = [
    "ui_agent", "domain_agent", "person_agent", "lead_scoring_agent",
    "competitor_agent", "pricing_agent", "compliance_agent", "retriever_agent",
    "summarizer_agent", "sentiment_agent", "meeting_notes_agent", "suggestion_agent",
    "ranking_agent", "action_item_agent", "followup_agent", "logger_agent"
]

# The base libraries every single agent needs
BASE_REQS = [
    "fastapi",
    "uvicorn[standard]",
    "redis",
    "python-dotenv"
]

# Agents that need to call an LLM (like OpenRouter)
LLM_AGENTS = [
    "summarizer_agent",
    "suggestion_agent",
    "action_item_agent",
    "ranking_agent" # Add any other agents that make API calls
]

# The extra library for LLM agents
LLM_REQS = [
    "requests",
    "openai" # The OpenRouter library uses the OpenAI client
]

def create_requirements_files():
    """Generates requirements.txt for all agent directories."""
    print("🚀 Starting to generate requirements.txt files...")
    backend_path = "backend"
    
    for agent_name in AGENTS:
        agent_path = os.path.join(backend_path, agent_name)
        if not os.path.exists(agent_path):
            print(f"⚠️ Warning: Directory not found for {agent_name}. Skipping.")
            continue
            
        # Determine the requirements for this agent
        current_reqs = BASE_REQS.copy()
        if agent_name in LLM_AGENTS:
            current_reqs.extend(LLM_REQS)
            
        # Write the requirements to the file
        req_file_path = os.path.join(agent_path, "requirements.txt")
        try:
            with open(req_file_path, "w") as f:
                for req in current_reqs:
                    f.write(f"{req}\n")
            print(f"✅ Successfully created requirements.txt for {agent_name}")
        except IOError as e:
            print(f"❌ Error creating file for {agent_name}: {e}")

    print("\n🎉 All done! Your agents are ready for installation.")

if __name__ == "__main__":
    create_requirements_files()