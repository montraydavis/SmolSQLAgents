import React from 'react';

const QueryInput = ({ 
  query, 
  setQuery, 
  executeQuery, 
  isLoading, 
  handleKeyPress 
}) => {
  return (
    <div className="card mb-3">
      <div className="card-header bg-white">
        <h5 className="mb-0">Natural Language Query</h5>
      </div>
      <div className="card-body">
        <div className="input-group">
          <input
            type="text"
            className="form-control"
            id="queryInput"
            placeholder="Ask a question about your data..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button
            className={`btn ${isLoading ? 'btn-info' : 'btn-primary'} position-relative`}
            type="button"
            onClick={executeQuery}
            disabled={isLoading || !query.trim()}
            style={{
              minWidth: '120px',
              transition: 'all 0.3s ease',
              borderRadius: '0 0.375rem 0.375rem 0'
            }}
          >
            {isLoading ? (
              <>
                <span 
                  className="spinner-border spinner-border-sm me-2" 
                  role="status" 
                  aria-hidden="true"
                  style={{ width: '1rem', height: '1rem' }}
                ></span>
                <span style={{ fontWeight: '500' }}>Running...</span>
              </>
            ) : (
              <>
                <i className="bi bi-play-fill me-2"></i>
                <span style={{ fontWeight: '500' }}>Run Query</span>
              </>
            )}
          </button>
        </div>
        <div className="mt-2 text-muted small">
          Example: "Show me the top 10 customers by total spending"
        </div>
      </div>
    </div>
  );
};

export default QueryInput; 