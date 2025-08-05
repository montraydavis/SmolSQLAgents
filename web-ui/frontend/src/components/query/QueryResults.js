import React from 'react';

const QueryResults = ({ queryExecution, results }) => {
  // Debug logging
  console.log('QueryResults - queryExecution:', queryExecution);
  console.log('QueryResults - results:', results);
  
  // Use results prop if available, otherwise fall back to queryExecution
  const displayResults = results || queryExecution?.sample_data?.sample_rows || [];
  const columns = queryExecution?.sample_data?.columns || [];
  
  console.log('QueryResults - displayResults:', displayResults);
  console.log('QueryResults - columns:', columns);
  
  if (!displayResults.length && !queryExecution) {
    console.log('QueryResults - returning null, no data to display');
    return null;
  }

  return (
    <div className="card mb-3">
      <div className="card-header bg-white">
        <h5 className="mb-0">
          <i className="bi bi-table me-2"></i>Query Results
        </h5>
      </div>
      <div className="card-body">
        <div className="table-responsive">
          <table className="table table-striped table-hover">
            <thead>
              <tr>
                {columns.map((column, index) => (
                  <th key={index}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayResults.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {Object.values(row).map((cell, cellIndex) => (
                    <td key={cellIndex}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-3 text-muted small">
          {displayResults.length} rows returned
          {queryExecution?.total_rows && queryExecution.total_rows !== displayResults.length && (
            <span className="ms-2 text-info">
              (showing {displayResults.length} of {queryExecution.total_rows} total rows)
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default QueryResults; 