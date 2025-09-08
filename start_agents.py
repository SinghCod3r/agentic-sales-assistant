#!/usr/bin/env python3
"""
Startup script for the Live Sales Assistant multi-agent system.
This script starts all agents in the correct order with proper port assignments.
"""

import subprocess
import time
import os
import sys
from pathlib import Path

# Agent configurations with their ports
AGENTS = [
    {"name": "ui_agent", "port": 8001, "path": "backend/ui_agent"},
    {"name": "domain_agent", "port": 8002, "path": "backend/domain_agent"},
    {"name": "person_agent", "port": 8003, "path": "backend/person_agent"},
    {"name": "lead_scoring_agent", "port": 8004, "path": "backend/lead_scoring_agent"},
    {"name": "competitor_agent", "port": 8005, "path": "backend/competitor_agent"},
    {"name": "pricing_agent", "port": 8006, "path": "backend/pricing_agent"},
    {"name": "compliance_agent", "port": 8007, "path": "backend/compliance_agent"},
    {"name": "retriever_agent", "port": 8008, "path": "backend/retriever_agent"},
    {"name": "summarizer_agent", "port": 8009, "path": "backend/summarizer_agent"},
    {"name": "sentiment_agent", "port": 8010, "path": "backend/sentiment_agent"},
    {"name": "meeting_notes_agent", "port": 8011, "path": "backend/meeting_notes_agent"},
    {"name": "suggestion_agent", "port": 8012, "path": "backend/suggestion_agent"},
    {"name": "ranking_agent", "port": 8013, "path": "backend/ranking_agent"},
    {"name": "action_item_agent", "port": 8014, "path": "backend/action_item_agent"},
    {"name": "followup_agent", "port": 8015, "path": "backend/followup_agent"},
    {"name": "logger_agent", "port": 8016, "path": "backend/logger_agent"},
]

def check_redis():
    """Check if Redis is running."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
        return True
    except Exception as e:
        print(f"❌ Redis is not running: {e}")
        print("Please start Redis before running the agents.")
        return False

def install_requirements(agent_path):
    """Install requirements for an agent."""
    requirements_file = os.path.join(agent_path, "requirements.txt")
    if os.path.exists(requirements_file):
        print(f"Installing requirements for {agent_path}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
                          cwd=agent_path, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install requirements for {agent_path}: {e}")
            # Continue anyway as requirements might already be installed

def start_agent(agent):
    """Start a single agent."""
    agent_path = agent["path"]
    port = agent["port"]
    name = agent["name"]
    
    if not os.path.exists(agent_path):
        print(f"❌ Agent path not found: {agent_path}")
        return None
    
    # Install requirements
    install_requirements(agent_path)
    
    # Start the agent
    print(f"🚀 Starting {name} on port {port}...")
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port), "--reload"],
            cwd=agent_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

def main():
    """Main function to start all agents."""
    print("🎯 Starting Live Sales Assistant Multi-Agent System")
    print("=" * 50)
    
    # Check Redis
    if not check_redis():
        sys.exit(1)
    
    # Start agents
    processes = []
    for agent in AGENTS:
        process = start_agent(agent)
        if process:
            processes.append((agent["name"], process))
        time.sleep(1)  # Small delay between starts
    
    print("\n✅ All agents started!")
    print("🌐 UI Agent available at: http://localhost:8001")
    print("📊 Frontend should be started separately with: cd frontend && npm start")
    print("\nPress Ctrl+C to stop all agents...")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all agents...")
        for name, process in processes:
            print(f"Stopping {name}...")
            process.terminate()
        print("✅ All agents stopped.")

if __name__ == "__main__":
    main()
