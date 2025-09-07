import React, { useState, useEffect, useMemo } from 'react';
import './App.css';

// CORRECTED: The agent IDs in this list now perfectly match the backend Python files.
const AGENT_WORKFLOW = [
  'ui_agent_v1',
  'domain_intelligence_agent_v1', // <-- This was the typo
  'person_enrichment_agent_v1',
  'compliance_agent_v1',
  'retriever_rag_agent_v1',
  'summarizer_agent_v1',
  'suggestion_agent_v1',
  'ranking_agent_v1',
];

function App() {
  const [inputValue, setInputValue] = useState('alex from google');
  const [events, setEvents] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [currentAgent, setCurrentAgent] = useState({ id: 'Offline', message: '' });

  // State for the progress bar
  const [isProcessing, setIsProcessing] = useState(false);
  const [completedSteps, setCompletedSteps] = useState(new Set());

  useEffect(() => {
    const eventSource = new EventSource('http://localhost:8001/stream');

    eventSource.onopen = () => {
      setEvents([{ agent_id: 'System', payload: { message: "SSE Connection Established!" } }]);
      setCurrentAgent({ id: 'System', message: 'Standing by for input...' });
    };

    eventSource.onmessage = (event) => {
      try {
        const eventData = JSON.parse(event.data);
        setEvents(prev => [eventData, ...prev]);
        setCurrentAgent({ id: eventData.agent_id, message: `Processed event on channel: ${eventData.channel}` });

        // Update progress bar state
        setCompletedSteps(prev => new Set(prev).add(eventData.agent_id));

        if (eventData.channel === 'suggestions.ranked') {
          setSuggestions(eventData.payload.suggestions || []);
          setIsProcessing(false); // Workflow complete
        }
      } catch (error) {
        console.error("Failed to parse event data:", error);
      }
    };

    eventSource.onerror = (error) => {
      console.error("EventSource failed:", error);
      setCurrentAgent({ id: 'Offline', message: 'Connection lost.' });
      setIsProcessing(false);
    };

    return () => eventSource.close();
  }, []);

  const handleSendMessage = async () => {
    if (!inputValue) return;
    // Reset state for a new workflow
    setSuggestions([]);
    setEvents([]);
    setCompletedSteps(new Set());
    setIsProcessing(true);

    try {
      const response = await fetch('http://localhost:8001/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputValue }),
      });
      if (!response.ok) throw new Error('Network response was not ok');
    } catch (error) {
      console.error("Failed to send trigger:", error);
      setIsProcessing(false);
    }
  };
  
  const onKeyPress = (event) => {
    if (event.key === 'Enter') handleSendMessage();
  };
  
  // Memoize the progress bar to prevent unnecessary re-renders
  const ProgressBar = useMemo(() => (
    <div className="progress-steps">
      {AGENT_WORKFLOW.map((agentId, index) => {
        const isCompleted = completedSteps.has(agentId);
        // Find the index of the *last* real agent event to determine the active step
        const lastCompletedIndex = AGENT_WORKFLOW.indexOf(events[0]?.agent_id);
        const isActive = index === lastCompletedIndex + 1;

        return (
          <div key={agentId} className={`step-item ${isCompleted ? 'completed' : ''} ${isActive && isProcessing ? 'active' : ''}`}>
            <div className="step-dot"></div>
            <div className="step-label">{agentId.replace(/_agent_v1|_intelligence/g, '')}</div>
          </div>
        );
      })}
    </div>
  ), [completedSteps, events, isProcessing]);


  return (
    <div className="App">
      <header>
        <h1>Agentic Live Sales Assistant For Hackathon</h1>
        <p>Team Name - Team Xspark</p>
      </header>

      <div className="container">
        <div className="left-panel">
          <div className="card">
            <h2>Mock STT Input</h2>
            <div className="input-group">
              <label>Enter a company and/or name to trigger the full agent workflow.</label>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={onKeyPress}
                disabled={isProcessing}
              />
              <button onClick={handleSendMessage} disabled={isProcessing}>
                {isProcessing ? 'Processing...' : 'Trigger Agents'}
              </button>
            </div>
          </div>

          {/* New Progress Bar Card */}
          {isProcessing && (
            <div className="card">
              <h2>Workflow Progress</h2>
              {ProgressBar}
            </div>
          )}

          <div className="card">
            <h2>Who's Thinking Now?</h2>
            <div className="status-indicator">{currentAgent.id}</div>
            <p className="status-message">{currentAgent.message}</p>
          </div>
        </div>

        <div className="right-panel">
          <div className="card">
            <h2>AI-Generated Talking Points</h2>
            <ul className="suggestions-list">
              {suggestions.length > 0 ? (
                suggestions.map((item, index) => (
                  <li key={index} className="suggestion-item">{item}</li>
                ))
              ) : (
                <li className="suggestion-item-empty">
                  {isProcessing ? 'Agents are working...' : 'Suggestions will appear here...'}
                </li>
              )}
            </ul>
          </div>
          <div className="card">
            <h2>Live Event Log (Provenance)</h2>
            <div className="event-log">
              {events.map((event, index) => (
                <div key={index} className="event-item">
                  <p className="event-agent-id">{`[${event.agent_id}]`}</p>
                  <pre className="event-payload">{JSON.stringify(event.payload, null, 2)}</pre>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

