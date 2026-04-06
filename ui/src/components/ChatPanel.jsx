import { useState, useRef, useEffect } from 'react';

export default function ChatPanel({ 
  chatLog, 
  onSendMessage, 
  activeDocument, 
  allDocuments = [] // Default to empty array to prevent undefined errors
}) {
  const [message, setMessage] = useState('');
  const [isCompareMode, setIsCompareMode] = useState(false);
  const chatBoxRef = useRef(null);

  // Safety check: Can only compare if we have at least 2 documents
  const canCompare = allDocuments.length >= 2;

  // Auto-scroll to bottom of chat
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [chatLog]);

  // If a user deletes a document and drops below 2, force Compare Mode off
  useEffect(() => {
    if (!canCompare && isCompareMode) {
      setIsCompareMode(false);
    }
  }, [canCompare, isCompareMode]);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed) return;

    onSendMessage(trimmed, isCompareMode);
    setMessage('');
  };

  return (
    <section className="panel right-panel">
      <div className="panel-header">
        <div className="header-flex">
          <div>
            <p className="label">AI Chat</p>
            <h2>{isCompareMode ? 'Legal Comparison' : 'Document Assistant'}</h2>
          </div>
          
          {/* Comparison Toggle */}
          <div className="toggle-container" title={!canCompare ? "Requires 2 documents" : ""}>
            <label className="switch">
              <input 
                type="checkbox" 
                checked={isCompareMode} 
                onChange={() => setIsCompareMode(!isCompareMode)} 
                disabled={!canCompare} // Disables if < 2 docs
              />
              <span className={`slider round ${!canCompare ? 'disabled' : ''}`}></span>
            </label>
            <span className={`toggle-label ${!canCompare ? 'muted' : ''}`}>Compare Mode</span>
          </div>
        </div>
      </div>

      {/* Context Indicator */}
      <div className={`context-chip ${isCompareMode ? 'compare-active' : ''}`}>
        {isCompareMode ? (
          <span>Comparing: <strong>{allDocuments.join(' vs ')}</strong></span>
        ) : (
          <span>Focus: <strong>{activeDocument === 'All Documents' ? 'Global Search' : activeDocument}</strong></span>
        )}
      </div>

      <div className="chat-box" ref={chatBoxRef}>
        {chatLog.length === 0 && (
          <div className="empty-state">
            <p>Ask a question about the {isCompareMode ? 'differences' : 'clauses'}...</p>
          </div>
        )}
        
        {chatLog.map((item, index) => (
          <div key={`${item.role}-${index}`} className={`chat-msg ${item.role}`}>
            <div className="msg-content">
              {typeof item.text === 'object' ? (
                <div className="json-response">
                   <p className="final-ans">{item.text.final_answer}</p>
                   
                   {/* Automatically renders the verdict if the backend sent one (Comparison Mode) */}
                   {item.text.verdict && (
                     <div className="verdict-box">
                       <strong>⚖️ Verdict:</strong> {item.text.verdict}
                     </div>
                   )}
                </div>
              ) : (
                item.text
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="chat-input-row tray">
        <input
          type="text"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={(event) => event.key === 'Enter' && handleSend()}
          placeholder={isCompareMode ? "e.g., How do these differ on late fees?" : "Ask about specific clauses..."}
        />
        <button 
          className={`btn ${isCompareMode ? 'secondary' : 'primary'}`} 
          onClick={handleSend}
        >
          {isCompareMode ? 'Compare' : 'Ask'}
        </button>
      </div>

      <style jsx>{`
        /* --- Layout & Typography --- */
        .header-flex { display: flex; justify-content: space-between; align-items: center; }
        .toggle-container { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; }
        .context-chip { padding: 8px 12px; font-size: 0.85rem; background: #f0f2f5; border-radius: 6px; margin: 10px 0; border-left: 4px solid #007bff; }
        .context-chip.compare-active { border-left-color: #ffc107; background: #fff9e6; }
        .empty-state { text-align: center; color: #888; margin-top: 50px; }
        .json-response { line-height: 1.5; }
        
        .verdict-box { margin-top: 10px; padding: 10px; background: #e8f4fd; border-radius: 6px; border: 1px solid #b3d7ff; color: #004085; font-size: 0.9rem;}
        .muted { color: #aaa; }

        /* --- Toggle Switch CSS --- */
        .switch { position: relative; display: inline-block; width: 44px; height: 24px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; }
        .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .4s; }
        
        input:checked + .slider { background-color: #007bff; }
        input:checked + .slider:before { transform: translateX(20px); }
        
        .slider.round { border-radius: 24px; }
        .slider.round:before { border-radius: 50%; }
        
        /* Disabled state styling */
        .slider.disabled { cursor: not-allowed; background-color: #e0e0e0; opacity: 0.6; }
      `}</style>
    </section>
  );
}