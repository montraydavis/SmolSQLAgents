import React, { useEffect, useCallback } from 'react';
import './ItemDetailsModal.css';

const ItemDetailsModal = ({
  showItemDetails,
  setShowItemDetails,
  selectedItem
}) => {
  // Prevent body scroll when modal is open
  useEffect(() => {
    if (showItemDetails) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showItemDetails]);

  // Memoized close handler to prevent unnecessary re-renders
  const handleClose = useCallback(() => {
    setShowItemDetails(false);
  }, [setShowItemDetails]);

  // Memoized backdrop click handler
  const handleBackdropClick = useCallback((e) => {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  }, [handleClose]);

  // Early return if modal should not be shown
  if (!showItemDetails || !selectedItem) {
    return null;
  }

  const renderTableDetails = () => {
    try {
      const table = selectedItem.table;
      if (!table) {
        return (
          <div className="alert alert-warning">
            <i className="bi bi-exclamation-triangle me-2"></i>
            <strong>No table data available</strong>
          </div>
        );
      }

      // Safely extract schema data with fallbacks
      const schemaData = table.schema || table.schema_data || {};
      let columns = [];
      
      // Handle different possible column data structures with proper null checks
      if (schemaData && schemaData.columns) {
        if (Array.isArray(schemaData.columns)) {
          columns = schemaData.columns.filter(col => col != null);
        } else if (typeof schemaData.columns === 'object') {
          columns = Object.values(schemaData.columns).filter(col => col != null);
        }
      } else if (Array.isArray(schemaData)) {
        columns = schemaData.filter(col => col != null);
      } else if (table.columns && Array.isArray(table.columns)) {
        columns = table.columns.filter(col => col != null);
      }
      
      // Ensure columns is always an array and filter out null/undefined values
      if (!Array.isArray(columns)) {
        columns = [];
      }
      
      // Calculate statistics with safe property access
      const columnCount = columns.length;
      const primaryKeys = columns.filter(col => col && (col.primary_key || col.is_primary_key)).length;
      const foreignKeys = columns.filter(col => col && (col.foreign_key || col.is_foreign_key)).length;
      const notNullColumns = columns.filter(col => col && col.nullable === false).length;

      return (
        <div>
          <h5 className="mb-3">Table Details</h5>
          
          {/* Business Purpose */}
          {table.business_purpose && (
            <div className="mb-3">
              <h6>Business Purpose</h6>
              <p className="text-muted">{table.business_purpose}</p>
            </div>
          )}

          {/* Documentation */}
          {table.documentation && (
            <div className="mb-3">
              <h6>Documentation</h6>
              <div className="bg-light p-3 rounded">
                <pre className="mb-0" style={{ whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
                  {table.documentation}
                </pre>
              </div>
            </div>
          )}

          {/* Statistics Cards */}
          <div className="row mb-4">
            <div className="col-md-3">
              <div className="text-center p-3 bg-primary bg-opacity-10 rounded">
                <div className="h3 text-primary">{columnCount}</div>
                <small className="text-muted">Columns</small>
              </div>
            </div>
            <div className="col-md-3">
              <div className="text-center p-3 bg-warning bg-opacity-10 rounded">
                <div className="h3 text-warning">{primaryKeys}</div>
                <small className="text-muted">Primary Keys</small>
              </div>
            </div>
            <div className="col-md-3">
              <div className="text-center p-3 bg-info bg-opacity-10 rounded">
                <div className="h3 text-info">{foreignKeys}</div>
                <small className="text-muted">Foreign Keys</small>
              </div>
            </div>
            <div className="col-md-3">
              <div className="text-center p-3 bg-success bg-opacity-10 rounded">
                <div className="h3 text-success">{notNullColumns}</div>
                <small className="text-muted">Not Null</small>
              </div>
            </div>
          </div>

          {/* Schema Information - Database IDE Style */}
          {columns.length > 0 && (
            <div className="mb-3">
              <h6>Schema Definition</h6>
              <div className="table-responsive">
                <table className="table table-sm table-striped">
                  <thead className="table-dark">
                    <tr>
                      <th style={{ width: '25%' }}>Column Name</th>
                      <th style={{ width: '20%' }}>Data Type</th>
                      <th style={{ width: '15%' }}>Nullable</th>
                      <th style={{ width: '15%' }}>Default</th>
                      <th style={{ width: '25%' }}>Constraints</th>
                    </tr>
                  </thead>
                  <tbody>
                    {columns.map((column, index) => {
                      if (!column) return null;
                      
                      const isPrimaryKey = column.primary_key || column.is_primary_key;
                      const isForeignKey = column.foreign_key || column.is_foreign_key;
                      
                      return (
                        <tr key={`${column.name || index}-${index}`} className={isPrimaryKey ? 'table-warning' : ''}>
                          <td>
                            <strong>{column.name || 'Unknown'}</strong>
                            {isPrimaryKey && (
                              <span className="badge bg-warning ms-1">PK</span>
                            )}
                            {isForeignKey && (
                              <span className="badge bg-info ms-1">FK</span>
                            )}
                          </td>
                          <td>
                            <code className="text-primary">{column.type || 'Unknown'}</code>
                          </td>
                          <td>
                            {column.nullable ? (
                              <span className="badge bg-success">NULL</span>
                            ) : (
                              <span className="badge bg-danger">NOT NULL</span>
                            )}
                          </td>
                          <td>
                            {column.default ? (
                              <code className="text-muted">{column.default}</code>
                            ) : (
                              <span className="text-muted">-</span>
                            )}
                          </td>
                          <td>
                            <div className="d-flex flex-wrap gap-1">
                              {isPrimaryKey && <span className="badge bg-warning">Primary Key</span>}
                              {isForeignKey && <span className="badge bg-info">Foreign Key</span>}
                              {column.unique && <span className="badge bg-secondary">Unique</span>}
                              {column.auto_increment && <span className="badge bg-dark">Auto Increment</span>}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* No Schema Data Message */}
          {columns.length === 0 && (
            <div className="mb-3">
              <div className="alert alert-warning">
                <i className="bi bi-exclamation-triangle me-2"></i>
                <strong>No schema data available</strong>
                <br />
                <small className="text-muted">
                  The table schema information could not be loaded. This might be because:
                  <ul className="mt-2 mb-0">
                    <li>The table hasn't been processed by the documentation system</li>
                    <li>The schema data is stored in a different format</li>
                    <li>There was an error loading the schema information</li>
                  </ul>
                </small>
              </div>
            </div>
          )}

          {/* Foreign Key Relationships */}
          {foreignKeys > 0 && (
            <div className="mb-3">
              <h6>Foreign Key Relationships</h6>
              <div className="table-responsive">
                <table className="table table-sm">
                  <thead className="table-light">
                    <tr>
                      <th>Column</th>
                      <th>References</th>
                      <th>On Delete</th>
                      <th>On Update</th>
                    </tr>
                  </thead>
                  <tbody>
                    {columns
                      .filter(col => col && (col.foreign_key || col.is_foreign_key))
                      .map((column, index) => (
                        <tr key={`fk-${column.name || index}-${index}`}>
                          <td><code>{column.name || 'Unknown'}</code></td>
                          <td>
                            {column.referenced_table && column.referenced_column ? (
                              <span>
                                <code>{column.referenced_table}</code>.<code>{column.referenced_column}</code>
                              </span>
                            ) : (
                              <span className="text-muted">Unknown</span>
                            )}
                          </td>
                          <td>
                            <span className="badge bg-secondary">
                              {column.on_delete || 'RESTRICT'}
                            </span>
                          </td>
                          <td>
                            <span className="badge bg-secondary">
                              {column.on_update || 'RESTRICT'}
                            </span>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Indexes */}
          {schemaData.indexes && Array.isArray(schemaData.indexes) && schemaData.indexes.length > 0 && (
            <div className="mb-3">
              <h6>Indexes</h6>
              <div className="table-responsive">
                <table className="table table-sm">
                  <thead className="table-light">
                    <tr>
                      <th>Index Name</th>
                      <th>Columns</th>
                      <th>Type</th>
                      <th>Unique</th>
                    </tr>
                  </thead>
                  <tbody>
                    {schemaData.indexes.map((index, indexIndex) => (
                      <tr key={`index-${index.name || indexIndex}-${indexIndex}`}>
                        <td><code>{index.name || 'Unknown'}</code></td>
                        <td>
                          {index.columns && Array.isArray(index.columns) ? (
                            index.columns.map(col => (
                              <span key={col} className="badge bg-light text-dark me-1">
                                {col}
                              </span>
                            ))
                          ) : (
                            <span className="text-muted">No columns</span>
                          )}
                        </td>
                        <td>
                          <span className="badge bg-info">{index.type || 'BTREE'}</span>
                        </td>
                        <td>
                          {index.unique ? (
                            <span className="badge bg-success">Yes</span>
                          ) : (
                            <span className="badge bg-secondary">No</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      );
    } catch (error) {
      console.error('Error rendering table details:', error);
      return (
        <div className="alert alert-danger">
          <i className="bi bi-exclamation-triangle me-2"></i>
          <strong>Error loading table details</strong>
          <br />
          <small className="text-muted">An error occurred while rendering the table information.</small>
        </div>
      );
    }
  };

  const renderRelationshipDetails = () => {
    try {
      const relationship = selectedItem.relationship;
      if (!relationship) {
        return (
          <div className="alert alert-warning">
            <i className="bi bi-exclamation-triangle me-2"></i>
            <strong>No relationship data available</strong>
          </div>
        );
      }

      return (
        <div>
          <h5 className="mb-3">Relationship Details</h5>
          
          {/* Relationship Type */}
          <div className="mb-3">
            <h6>Type</h6>
            <span className="badge bg-primary">{relationship.relationship_type || 'Unknown'}</span>
          </div>

          {/* Constrained Table */}
          <div className="mb-3">
            <h6>Constrained Table</h6>
            <p className="mb-1">
              <strong>{relationship.constrained_table}</strong>
            </p>
            {relationship.constrained_columns && (
              <div>
                <small className="text-muted">Columns: {relationship.constrained_columns.join(', ')}</small>
              </div>
            )}
          </div>

          {/* Referred Table */}
          <div className="mb-3">
            <h6>Referred Table</h6>
            <p className="mb-1">
              <strong>{relationship.referred_table}</strong>
            </p>
            {relationship.referred_columns && (
              <div>
                <small className="text-muted">Columns: {relationship.referred_columns.join(', ')}</small>
              </div>
            )}
          </div>

          {/* Documentation */}
          {relationship.documentation && (
            <div className="mb-3">
              <h6>Documentation</h6>
              <p className="text-muted">{relationship.documentation}</p>
            </div>
          )}
        </div>
      );
    } catch (error) {
      console.error('Error rendering relationship details:', error);
      return (
        <div className="alert alert-danger">
          <i className="bi bi-exclamation-triangle me-2"></i>
          <strong>Error loading relationship details</strong>
          <br />
          <small className="text-muted">An error occurred while rendering the relationship information.</small>
        </div>
      );
    }
  };

  return (
    <>
      <div className="modal fade show" style={{ display: 'block' }} tabIndex="-1">
        <div className="modal-dialog modal-lg">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">
                <i className={`bi ${selectedItem.type === 'table' ? 'bi-table' : 'bi-arrow-right'} me-2`}></i>
                {selectedItem.name || 'Unknown Item'}
              </h5>
              <button
                type="button"
                className="btn-close"
                onClick={handleClose}
                aria-label="Close"
              ></button>
            </div>
            <div className="modal-body">
              {selectedItem.description && (
                <div className="mb-3">
                  <h6>Description</h6>
                  <p className="text-muted">{selectedItem.description}</p>
                </div>
              )}
              
              {selectedItem.type === 'table' ? renderTableDetails() : renderRelationshipDetails()}
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-secondary" onClick={handleClose}>
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="modal-backdrop fade show" onClick={handleBackdropClick}></div>
    </>
  );
};

export default ItemDetailsModal; 