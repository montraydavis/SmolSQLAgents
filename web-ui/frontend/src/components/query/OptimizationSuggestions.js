import React from 'react';

const OptimizationSuggestions = ({ optimizationSuggestions }) => {
  if (!optimizationSuggestions || optimizationSuggestions.length === 0) return null;

  return (
    <div className="card mb-3">
      <div className="card-header bg-white">
        <h5 className="mb-0">
          <i className="bi bi-speedometer2 me-2"></i>Optimization Suggestions
        </h5>
      </div>
      <div className="card-body">
        <div className="row">
          {optimizationSuggestions.map((suggestion, index) => (
            <div key={index} className="col-md-6 mb-3">
              <div className="card border-warning">
                <div className="card-body">
                  <h6 className="card-title">
                    <i className="bi bi-lightbulb text-warning me-2"></i>
                    {suggestion.type}
                  </h6>
                  <p className="card-text">{suggestion.description}</p>
                  {suggestion.sql && (
                    <pre className="bg-light p-2 rounded small">
                      <code>{suggestion.sql}</code>
                    </pre>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OptimizationSuggestions; 