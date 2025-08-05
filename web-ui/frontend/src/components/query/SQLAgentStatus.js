import React from 'react';

const SQLAgentStatus = ({ sqlAgentStatus }) => {
  if (!sqlAgentStatus) return null;

  return (
    <div className="card mb-3">
      <div className="card-header bg-white">
        <h5 className="mb-0">
          <i className="bi bi-robot me-2"></i>SQL Agent Status
        </h5>
      </div>
      <div className="card-body">
        <div className="row">
          <div className="col-md-6">
            <h6>Features</h6>
            <div className="d-flex flex-wrap gap-2">
              {Object.entries(sqlAgentStatus.features || {}).map(([feature, available]) => (
                <span key={feature} className={`badge ${available ? 'bg-success' : 'bg-secondary'}`}>
                  {available ? '✅' : '❌'} {feature.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
          <div className="col-md-6">
            <h6>Agents</h6>
            <div className="d-flex flex-wrap gap-2">
              {Object.entries(sqlAgentStatus.agents || {}).map(([agent, available]) => (
                <span key={agent} className={`badge ${available ? 'bg-success' : 'bg-secondary'}`}>
                  {available ? '✅' : '❌'} {agent.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Show informative message when SQL Agents are not available */}
        {!sqlAgentStatus.sql_agents_available && (
          <div className="mt-3 p-3 bg-light rounded">
            <div className="d-flex align-items-center">
              <i className="bi bi-exclamation-triangle text-warning me-2"></i>
              <div>
                <strong>SQL Agents Not Available</strong>
                <br />
                <small className="text-muted">
                  SQL Agents are not available. Please ensure the backend server is running and SQL Agents are properly initialized.
                </small>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SQLAgentStatus; 