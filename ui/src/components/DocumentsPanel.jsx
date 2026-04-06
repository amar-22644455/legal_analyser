export default function DocumentsPanel({
  uploadedDocuments,
  selectedFiles,
  setSelectedFiles,
  uploadStatus,
  activeDocument,
  setActiveDocument,
  documentCountLabel,
  onUpload,
  onReset,
  isUploading
}) {
  return (
    <section className="panel left-panel">
      <div className="panel-header">
        <p className="label">Storage & Analysis</p>
        <h1>Legal Workspace</h1>
      </div>

      <div className="card table-card">
        <div className="card-title-row">
          <p className="meta">Active Files</p>
          <span className="status-chip">{documentCountLabel}</span>
        </div>

        <div className="document-table-head">
          <span>Document Name</span>
          <span>Status</span>
        </div>

        <div className="document-list">
          {uploadedDocuments.length === 0 ? (
            <div className="empty-row muted">No documents analyzed yet.</div>
          ) : (
            <>
              {/* CRITICAL ADDITION: The Comparison Button */}
              {/* This only shows up when exactly 2 documents are uploaded */}
              {uploadedDocuments.length === 2 && (
                <button
                  type="button"
                  className={`document-row compare-row ${activeDocument === 'All Documents' ? 'active' : ''}`}
                  onClick={() => setActiveDocument('All Documents')}
                >
                  <span className="doc-name">
                    <span className="icon">⚖️</span> Compare Both Documents
                  </span>
                  <span className="doc-status bold-status">Ready</span>
                </button>
              )}

              {/* Individual Document Rows */}
              {uploadedDocuments.map((name, index) => (
                <button
                  type="button"
                  key={`${name}-${index}`}
                  className={`document-row ${activeDocument === name ? 'active' : ''}`}
                  onClick={() => setActiveDocument(name)}
                >
                  <span className="doc-name">
                    <span className="icon">📄</span> {name}
                  </span>
                  <span className="doc-status">Analyzed</span>
                </button>
              ))}
            </>
          )}
        </div>
      </div>

      <div className="card">
        <p className="meta">Add Source</p>
        <div className="drop-zone">
          <div className="drop-icon">☁</div>
          <p className="drop-title">Upload Legal Docs</p>
          <label className="btn primary upload-trigger">
            Choose Files
            <input
              type="file"
              multiple
              accept=".pdf,.txt,.png,.jpg,.jpeg" // Added to match backend capabilities
              onChange={(event) => {
                const filesArray = Array.from(event.target.files || []);
                setSelectedFiles((prev) => {
                  const prevNames = prev.map((f) => f.name);
                  const newFiles = filesArray.filter((f) => !prevNames.includes(f.name));
                  return [...prev, ...newFiles];
                });
                event.target.value = null; 
              }}
              style={{ display: 'none' }} // Hides the ugly default file input text
            />
          </label>
        </div>

        {selectedFiles.length > 0 && (
          <p className="muted pending-files">Selected: {selectedFiles.map((item) => item.name).join(', ')}</p>
        )}

        <div className="actions-row upload-actions">
          <button className="btn primary full-width" onClick={onUpload} disabled={isUploading || selectedFiles.length === 0}>
            {isUploading ? 'Uploading & Analyzing...' : 'Upload & Analyze'}
          </button>
          <button className="btn ghost" onClick={onReset}>Clear All</button>
        </div>

        <p className="status-text">{uploadStatus}</p>
      </div>

      <style jsx>{`
        .table-card { padding: 0; overflow: hidden; }
        .card-title-row { padding: 16px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f0f0f0; }
        .document-table-head { display: grid; grid-template-columns: 1fr 80px; padding: 8px 16px; background: #fafbfc; font-size: 0.75rem; color: #666; font-weight: 600; }
        .document-row { width: 100%; display: grid; grid-template-columns: 1fr 80px; padding: 12px 16px; border: none; background: none; text-align: left; cursor: pointer; border-bottom: 1px solid #f6f8fa; align-items: center; }
        .document-row:hover { background: #f0f4f8; }
        .document-row.active { background: #f0f7ff; border-left: 4px solid #007bff; }
        
        .compare-row { background: #fff9e6; border-bottom: 1px solid #ffeeba; }
        .compare-row.active { background: #fff3cd; border-left: 4px solid #ffc107; }
        .bold-status { color: #856404; font-weight: 700; }
        
        .icon { margin-right: 6px; }
        .doc-name { font-size: 0.85rem; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500; }
        .doc-status { font-size: 0.75rem; color: #28a745; text-align: right; }
        .full-width { width: 100%; justify-content: center; margin-right: 10px; }
        .status-text { font-size: 0.8rem; margin-top: 10px; color: #666; text-align: center; }
      `}</style>
    </section>
  );
}