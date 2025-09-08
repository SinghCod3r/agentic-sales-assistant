# New Agents Added to Live Sales Assistant

This document describes the 6 new agents that have been added to enhance the sales assistant system.

## New Agents Overview

### 1. Sentiment Analysis Agent (`sentiment_agent`)
- **Port**: 8010
- **Listens to**: `summary.created`
- **Publishes to**: `sentiment.analyzed`
- **Purpose**: Analyzes the emotional tone and sentiment of sales conversations
- **Output**: Sentiment classification, confidence score, detected emotions, and analysis summary

### 2. Competitor Intelligence Agent (`competitor_agent`)
- **Port**: 8005
- **Listens to**: `domain.fetched`
- **Publishes to**: `competitor.analyzed`
- **Purpose**: Provides competitive analysis and strategic insights
- **Output**: Strengths/weaknesses analysis, competitive positioning, strategic recommendations

### 3. Pricing Intelligence Agent (`pricing_agent`)
- **Port**: 8006
- **Listens to**: `competitor.analyzed`
- **Publishes to**: `pricing.strategy_generated`
- **Purpose**: Generates pricing strategies based on competitor analysis
- **Output**: Pricing recommendations, competitive advantages, negotiation tips

### 4. Lead Scoring Agent (`lead_scoring_agent`)
- **Port**: 8004
- **Listens to**: `person.enriched`
- **Publishes to**: `lead.scored`
- **Purpose**: Scores leads based on person and company information
- **Output**: Lead score (0-100), qualification status, next steps, risk factors

### 5. Meeting Notes Agent (`meeting_notes_agent`)
- **Port**: 8011
- **Listens to**: `summary.created`
- **Publishes to**: `meeting.notes_structured`
- **Purpose**: Structures conversation summaries into organized meeting notes
- **Output**: Attendees, key topics, decisions made, action items, key quotes

### 6. Follow-up Agent (`followup_agent`)
- **Port**: 8015
- **Listens to**: `action_items.created`
- **Publishes to**: `followup.plan_generated`
- **Purpose**: Creates comprehensive follow-up plans based on action items
- **Output**: Timeline-based action plan, reminders, priority levels, success metrics

## Enhanced Workflow

The new workflow now includes these additional steps:

1. UI Agent (triggers workflow)
2. Domain Intelligence Agent (fetches company info)
3. Person Enrichment Agent (enriches person data)
4. **Lead Scoring Agent** (scores the lead)
5. **Competitor Intelligence Agent** (analyzes competition)
6. **Pricing Intelligence Agent** (generates pricing strategy)
7. Compliance Agent (checks for PII)
8. Retriever RAG Agent (retrieves documents)
9. Summarizer Agent (summarizes content)
10. **Sentiment Analysis Agent** (analyzes conversation tone)
11. **Meeting Notes Agent** (structures meeting notes)
12. Suggestion Agent (generates talking points)
13. Ranking Agent (ranks suggestions)
14. Action Item Agent (creates action items)
15. **Follow-up Agent** (creates follow-up plan)
16. Logger Agent (logs all events)

## Setup Instructions

1. **Install Dependencies**: Each new agent has its own `requirements.txt` file
2. **Environment Variables**: Copy `.env.template` to `.env` and add your OpenRouter API key
3. **Start Agents**: Use the provided `start_agents.py` script or start each agent manually
4. **Frontend**: The frontend has been updated to include the new agents in the workflow

## Manual Agent Startup

To start each agent manually:

```bash
# Navigate to each agent directory and run:
cd backend/sentiment_agent
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8010 --reload

# Repeat for other agents with their respective ports
```

## API Key Requirements

The following agents require an OpenRouter API key:
- sentiment_agent
- competitor_agent
- pricing_agent
- lead_scoring_agent
- meeting_notes_agent
- followup_agent

## Benefits of New Agents

1. **Enhanced Intelligence**: More comprehensive analysis of sales conversations
2. **Better Lead Qualification**: Automated lead scoring helps prioritize prospects
3. **Competitive Advantage**: Real-time competitor analysis and pricing strategies
4. **Improved Follow-up**: Structured follow-up plans ensure no opportunities are missed
5. **Better Meeting Management**: Organized meeting notes and sentiment analysis
6. **Complete Sales Cycle**: End-to-end support from initial contact to follow-up

## Error Handling

All new agents include robust error handling:
- Graceful fallback when API keys are not configured
- Mock responses for demonstration purposes
- Comprehensive error logging
- Timeout handling for API calls

## Monitoring

The Logger Agent captures all events from the new agents, providing complete audit trails and system monitoring capabilities.
