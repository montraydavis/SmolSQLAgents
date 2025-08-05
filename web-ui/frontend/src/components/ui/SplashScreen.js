import React from 'react';

const SplashScreen = ({ 
  splashStatus, 
  splashMessage, 
  splashProgress, 
  pollingAttempts, 
  retryInitialization 
}) => {
  return (
    <div className="splash-screen">
      <div className="splash-content">
        <div className="splash-logo">
          <i className="bi bi-database-gear"></i>
          <h1>SQL Agent</h1>
          <p>Natural Language to SQL Pipeline</p>
        </div>

        <div className="splash-status">
          <div className="status-indicator">
            {splashStatus === 'checking' && (
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            )}
            {splashStatus === 'error' && (
              <i className="bi bi-exclamation-triangle text-danger"></i>
            )}
          </div>

          <h3>{splashMessage}</h3>

          <div className="progress mt-3" style={{ height: '4px' }}>
            <div
              className="progress-bar"
              role="progressbar"
              style={{ width: `${splashProgress}%` }}
              aria-valuenow={splashProgress}
              aria-valuemin="0"
              aria-valuemax="100"
            ></div>
          </div>

          {splashStatus === 'checking' && (
            <div className="mt-3">
              <small className="text-muted">
                <i className="bi bi-info-circle me-1"></i>
                Automatically retrying connection... (attempt {pollingAttempts}/30)
              </small>
            </div>
          )}

          {splashStatus === 'error' && (
            <div className="mt-4">
              <button
                className="btn btn-primary"
                onClick={retryInitialization}
              >
                <i className="bi bi-arrow-clockwise me-2"></i>
                Retry Connection
              </button>
              <div className="mt-3">
                <small className="text-muted">
                  <i className="bi bi-lightbulb me-1"></i>
                  Make sure the backend server is running at http://127.0.0.1:5000
                </small>
                <br />
                <small className="text-muted">
                  <i className="bi bi-clock me-1"></i>
                  The app will automatically retry for 30 seconds
                </small>
              </div>
            </div>
          )}
        </div>

        <div className="splash-footer">
          <small className="text-muted">
            Powered by smol-sql-agents
          </small>
        </div>
      </div>
    </div>
  );
};

export default SplashScreen; 