export default function SummaryPanel({
  activeDocument,
  summary,
  importantPoints,
  analysisNotes,
  riskScore,
  isAnalyzing // This is now tied to the upload process!
}) {
  return (
    <section className="panel middle-panel">
      <div className="panel-header middle-head flex">
        <div>
          <p className="label flex-1">Document Summary</p>
        </div>
        {/* If the system is processing an upload, show a loading indicator */}
        {isAnalyzing && (
          <span className="analyzing-indicator">🔄 Analyzing...</span>
        )}
      </div>

      <div className="middle-content">
        {/* Status Card */}
        <div className="card">
          <p className="section-title">Analysis Status</p>
          <ul className="bullet-list executive-list">
            {analysisNotes.map((note, index) => (
              <li key={`${note}-${index}`}>{note}</li>
            ))}
          </ul>
        </div>

        {/* Summary Card */}
        <div className="card">
          <div className="summary-header-row">
            <p className="section-title">Selected Document: {activeDocument}</p>
            
            {/* Updated Risk Badge: Now handles string values */}
            {riskScore !== '--' && (
              <span className={`summary-badge ${riskScore === 'High Risk' ? 'danger' : 'safe'}`}>
                {riskScore}
              </span>
            )}
          </div>
          <div className="document-preview">
            <p className="summary-text">{summary}</p>
          </div>
        </div>

        {/* Key Points Card */}
        <div className="card">
          <p className="section-title">Important Points</p>
          {importantPoints.length === 0 ? (
            <p className="muted">Upload and select a document to view key clauses and risks.</p>
          ) : (
            <ul className="points-list bullet-list">
              {importantPoints.map((point, index) => (
                <li key={`${point}-${index}`}>{point}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Updated Risk Pill */}
      <div className={`risk-pill ${riskScore === 'High Risk' ? 'danger-pill' : ''}`}>
        Overall Risk Level: {riskScore}
      </div>

      <style jsx>{`
        .middle-head { display: flex; justify-content: space-between; align-items: center; }
        .analyzing-indicator { font-size: 0.85rem; color: #007bff; font-weight: 600; animation: pulse 1.5s infinite; }
        .summary-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        
        .summary-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; }
        .summary-badge.danger { background-color: #ffe5e5; color: #d93025; }
        .summary-badge.safe { background-color: #e6f4ea; color: #1e8e3e; }
        
        .risk-pill { padding: 8px 16px; border-radius: 20px; background: #f1f3f4; font-weight: 600; font-size: 0.9rem; text-align: center; margin-top: auto; }
        .risk-pill.danger-pill { background-color: #ffe5e5; color: #d93025; }
        
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </section>
  );
}