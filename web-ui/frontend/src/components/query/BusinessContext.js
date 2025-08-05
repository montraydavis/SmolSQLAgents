import React from 'react';

const BusinessContext = ({ businessContext }) => {
  if (!businessContext) return null;

  return (
    <div className="card mb-3">
      <div className="card-header bg-white">
        <h5 className="mb-0">
          <i className="bi bi-lightbulb me-2"></i>Business Context
        </h5>
      </div>
      <div className="card-body">
        <p className="mb-2">{businessContext.context}</p>
        <div className="d-flex flex-wrap gap-2">
          {businessContext.relevant_tables?.map((table, index) => (
            <span key={index} className="badge bg-secondary">{table}</span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BusinessContext; 