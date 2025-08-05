import React, { useState, useEffect } from 'react';
import './DocumentationPage.css';

const DocumentationPage = () => {
  const [documentationData, setDocumentationData] = useState({
    tables: [],
    relationships: [],
    summaries: []
  });
  const [filteredData, setFilteredData] = useState({
    tables: [],
    relationships: [],
    summaries: []
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedItem, setSelectedItem] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('tables');

  useEffect(() => {
    loadDocumentationData();
  }, []);

  useEffect(() => {
    filterData();
  }, [documentationData, searchQuery, selectedCategory]);

  const loadDocumentationData = async () => {
    setIsLoading(true);
    try {
      // Load summaries (documented items)
      const summariesResponse = await fetch('http://127.0.0.1:5000/api/documentation/summaries');
      let summaries = [];
      
      if (summariesResponse.ok) {
        const summariesData = await summariesResponse.json();
        if (summariesData.success && summariesData.summaries) {
          summaries = Object.values(summariesData.summaries);
        }
      }

      // Load schema data as fallback
      const schemaResponse = await fetch('http://127.0.0.1:5000/api/schema');
      let tables = [];
      let relationships = [];
      
      if (schemaResponse.ok) {
        const schemaData = await schemaResponse.json();
        if (schemaData.success) {
          tables = schemaData.tables || [];
          relationships = schemaData.relationships || [];
        }
      }

      // Combine and organize data
      const organizedData = {
        tables: [...summaries.filter(item => item.type === 'table'), ...tables],
        relationships: [...summaries.filter(item => item.type === 'relationship'), ...relationships],
        summaries: summaries
      };

      setDocumentationData(organizedData);
    } catch (error) {
      console.error('Error loading documentation data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterData = () => {
    const query = searchQuery.toLowerCase();
    const category = selectedCategory;

    const filterItems = (items) => {
      return items.filter(item => {
        const matchesQuery = !query || 
          item.name?.toLowerCase().includes(query) ||
          item.table_name?.toLowerCase().includes(query) ||
          item.business_purpose?.toLowerCase().includes(query) ||
          item.documentation?.toLowerCase().includes(query) ||
          item.relationship_type?.toLowerCase().includes(query) ||
          item.constrained_table?.toLowerCase().includes(query) ||
          item.referred_table?.toLowerCase().includes(query);

        const matchesCategory = category === 'all' || 
          (category === 'tables' && (item.type === 'table' || item.columns)) ||
          (category === 'relationships' && (item.type === 'relationship' || item.constrained_table));

        return matchesQuery && matchesCategory;
      });
    };

    setFilteredData({
      tables: filterItems(documentationData.tables),
      relationships: filterItems(documentationData.relationships),
      summaries: filterItems(documentationData.summaries)
    });
  };

  const handleItemClick = (item) => {
    setSelectedItem(item);
    setShowDetails(true);
  };

  const closeDetails = () => {
    setShowDetails(false);
    setSelectedItem(null);
  };

  const getItemType = (item) => {
    if (item.type === 'table' || item.columns) return 'table';
    if (item.type === 'relationship' || item.constrained_table) return 'relationship';
    return 'summary';
  };

  const getItemIcon = (item) => {
    const type = getItemType(item);
    switch (type) {
      case 'table':
        return 'bi-table';
      case 'relationship':
        return 'bi-arrow-right';
      default:
        return 'bi-file-text';
    }
  };

  const getItemTitle = (item) => {
    return item.name || item.table_name || `${item.constrained_table} → ${item.referred_table}` || 'Unknown';
  };

  const getItemDescription = (item) => {
    return item.business_purpose || item.documentation || item.relationship_type || 'No description available';
  };

  const getStatusBadge = (item) => {
    if (item.status === 'completed') {
      return <span className="badge bg-success">Complete</span>;
    } else if (item.status === 'pending') {
      return <span className="badge bg-warning">Pending</span>;
    } else if (item.status === 'failed') {
      return <span className="badge bg-danger">Failed</span>;
    }
    return <span className="badge bg-secondary">Unknown</span>;
  };

  if (isLoading) {
    return (
      <div className="documentation-page">
        <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="documentation-page">
      {/* Header */}
      <div className="page-header">
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <h2 className="mb-1">
              <i className="bi bi-journal-text me-2"></i>
              Database Documentation
            </h2>
            <p className="text-muted mb-0">
              {filteredData.tables.length + filteredData.relationships.length} documented items
            </p>
          </div>
          <button 
            className="btn btn-outline-primary"
            onClick={loadDocumentationData}
          >
            <i className="bi bi-arrow-clockwise me-1"></i>
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="row g-3">
          <div className="col-md-6">
            <div className="input-group">
              <span className="input-group-text">
                <i className="bi bi-search"></i>
              </span>
              <input
                type="text"
                className="form-control"
                placeholder="Search documentation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
          <div className="col-md-3">
            <select
              className="form-select"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              <option value="tables">Tables</option>
              <option value="relationships">Relationships</option>
            </select>
          </div>
          <div className="col-md-3">
            <button 
              className="btn btn-outline-secondary w-100"
              onClick={() => {
                setSearchQuery('');
                setSelectedCategory('all');
              }}
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Content Tabs */}
      <div className="content-tabs">
        <ul className="nav nav-tabs" role="tablist">
          <li className="nav-item" role="presentation">
            <button
              className={`nav-link ${activeTab === 'tables' ? 'active' : ''}`}
              onClick={() => setActiveTab('tables')}
            >
              <i className="bi bi-table me-1"></i>
              Tables ({filteredData.tables.length})
            </button>
          </li>
          <li className="nav-item" role="presentation">
            <button
              className={`nav-link ${activeTab === 'relationships' ? 'active' : ''}`}
              onClick={() => setActiveTab('relationships')}
            >
              <i className="bi bi-arrow-right me-1"></i>
              Relationships ({filteredData.relationships.length})
            </button>
          </li>
          <li className="nav-item" role="presentation">
            <button
              className={`nav-link ${activeTab === 'summaries' ? 'active' : ''}`}
              onClick={() => setActiveTab('summaries')}
            >
              <i className="bi bi-file-text me-1"></i>
              All Documentation ({filteredData.summaries.length})
            </button>
          </li>
        </ul>
      </div>

      {/* Content Area */}
      <div className="content-area">
        {activeTab === 'tables' && (
          <div className="items-grid">
            {filteredData.tables.length > 0 ? (
              <div className="row g-4">
                {filteredData.tables.map((item, index) => (
                  <div key={index} className="col-lg-6 col-xl-4">
                    <div 
                      className="documentation-card"
                      onClick={() => handleItemClick(item)}
                    >
                      <div className="card h-100">
                        <div className="card-header d-flex justify-content-between align-items-center">
                          <span className="badge bg-primary">
                            <i className={`bi ${getItemIcon(item)} me-1`}></i>
                            Table
                          </span>
                          {getStatusBadge(item)}
                        </div>
                        <div className="card-body">
                          <h6 className="card-title">{getItemTitle(item)}</h6>
                          <p className="card-text text-muted">
                            {getItemDescription(item).length > 100 
                              ? `${getItemDescription(item).substring(0, 100)}...`
                              : getItemDescription(item)}
                          </p>
                          {item.column_count && (
                            <div className="mt-2">
                              <small className="text-muted">
                                {item.column_count} columns
                              </small>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="text-center py-5">
                  <i className="bi bi-table display-1 text-muted"></i>
                  <h4 className="mt-3">No tables found</h4>
                  <p className="text-muted">
                    {searchQuery || selectedCategory !== 'all' 
                      ? 'Try adjusting your search criteria or filters.'
                      : 'No table documentation is currently available.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'relationships' && (
          <div className="items-grid">
            {filteredData.relationships.length > 0 ? (
              <div className="row g-4">
                {filteredData.relationships.map((item, index) => (
                  <div key={index} className="col-lg-6 col-xl-4">
                    <div 
                      className="documentation-card"
                      onClick={() => handleItemClick(item)}
                    >
                      <div className="card h-100">
                        <div className="card-header d-flex justify-content-between align-items-center">
                          <span className="badge bg-info">
                            <i className={`bi ${getItemIcon(item)} me-1`}></i>
                            Relationship
                          </span>
                          {getStatusBadge(item)}
                        </div>
                        <div className="card-body">
                          <h6 className="card-title">{getItemTitle(item)}</h6>
                          <p className="card-text text-muted">
                            {getItemDescription(item).length > 100 
                              ? `${getItemDescription(item).substring(0, 100)}...`
                              : getItemDescription(item)}
                          </p>
                          {item.relationship_type && (
                            <div className="mt-2">
                              <small className="text-muted">
                                Type: {item.relationship_type}
                              </small>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="text-center py-5">
                  <i className="bi bi-arrow-right display-1 text-muted"></i>
                  <h4 className="mt-3">No relationships found</h4>
                  <p className="text-muted">
                    {searchQuery || selectedCategory !== 'all' 
                      ? 'Try adjusting your search criteria or filters.'
                      : 'No relationship documentation is currently available.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'summaries' && (
          <div className="items-grid">
            {filteredData.summaries.length > 0 ? (
              <div className="row g-4">
                {filteredData.summaries.map((item, index) => (
                  <div key={index} className="col-lg-6 col-xl-4">
                    <div 
                      className="documentation-card"
                      onClick={() => handleItemClick(item)}
                    >
                      <div className="card h-100">
                        <div className="card-header d-flex justify-content-between align-items-center">
                          <span className={`badge bg-${getItemType(item) === 'table' ? 'primary' : 'info'}`}>
                            <i className={`bi ${getItemIcon(item)} me-1`}></i>
                            {getItemType(item) === 'table' ? 'Table' : 'Relationship'}
                          </span>
                          {getStatusBadge(item)}
                        </div>
                        <div className="card-body">
                          <h6 className="card-title">{getItemTitle(item)}</h6>
                          <p className="card-text text-muted">
                            {getItemDescription(item).length > 100 
                              ? `${getItemDescription(item).substring(0, 100)}...`
                              : getItemDescription(item)}
                          </p>
                          {item.processed_at && (
                            <div className="mt-2">
                              <small className="text-muted">
                                Processed: {new Date(item.processed_at).toLocaleDateString()}
                              </small>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="text-center py-5">
                  <i className="bi bi-file-text display-1 text-muted"></i>
                  <h4 className="mt-3">No documentation found</h4>
                  <p className="text-muted">
                    {searchQuery || selectedCategory !== 'all' 
                      ? 'Try adjusting your search criteria or filters.'
                      : 'No documentation is currently available.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Item Details Modal */}
      {showDetails && selectedItem && (
        <div className="modal fade show" style={{ display: 'block' }} tabIndex="-1">
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className={`bi ${getItemIcon(selectedItem)} me-2`}></i>
                  {getItemTitle(selectedItem)}
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={closeDetails}
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body">
                <div className="row">
                  <div className="col-md-8">
                    <h6>Business Purpose</h6>
                    <p className="text-muted">
                      {selectedItem.business_purpose || 'No business purpose documented.'}
                    </p>

                    <h6 className="mt-4">Documentation</h6>
                    <div className="bg-light p-3 rounded">
                      <p className="mb-0">
                        {selectedItem.documentation || 'No detailed documentation available.'}
                      </p>
                    </div>

                    {getItemType(selectedItem) === 'table' && selectedItem.columns && (
                      <>
                        <h6 className="mt-4">Schema Information</h6>
                        <div className="table-responsive">
                          <table className="table table-sm">
                            <thead>
                              <tr>
                                <th>Column</th>
                                <th>Type</th>
                                <th>Nullable</th>
                                <th>Primary Key</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedItem.columns.map((col, index) => (
                                <tr key={index}>
                                  <td><code>{col.name}</code></td>
                                  <td><code>{col.type}</code></td>
                                  <td>
                                    <span className={`badge ${col.nullable ? 'bg-success' : 'bg-danger'}`}>
                                      {col.nullable ? 'NULL' : 'NOT NULL'}
                                    </span>
                                  </td>
                                  <td>
                                    {col.primary_key && <span className="badge bg-warning">PK</span>}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </>
                    )}

                    {getItemType(selectedItem) === 'relationship' && (
                      <>
                        <h6 className="mt-4">Relationship Details</h6>
                        <div className="row">
                          <div className="col-md-6">
                            <strong>From:</strong> {selectedItem.constrained_table}
                            {selectedItem.constrained_columns && (
                              <div className="small text-muted">
                                Columns: {selectedItem.constrained_columns.join(', ')}
                              </div>
                            )}
                          </div>
                          <div className="col-md-6">
                            <strong>To:</strong> {selectedItem.referred_table}
                            {selectedItem.referred_columns && (
                              <div className="small text-muted">
                                Columns: {selectedItem.referred_columns.join(', ')}
                              </div>
                            )}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                  <div className="col-md-4">
                    <h6>Metadata</h6>
                    <ul className="list-unstyled">
                      <li><strong>Type:</strong> {getItemType(selectedItem)}</li>
                      <li><strong>Status:</strong> {getStatusBadge(selectedItem)}</li>
                      {selectedItem.processed_at && (
                        <li><strong>Processed:</strong> {new Date(selectedItem.processed_at).toLocaleString()}</li>
                      )}
                      {selectedItem.column_count && (
                        <li><strong>Columns:</strong> {selectedItem.column_count}</li>
                      )}
                      {selectedItem.relationship_type && (
                        <li><strong>Relationship Type:</strong> {selectedItem.relationship_type}</li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={closeDetails}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Modal Backdrop */}
      {showDetails && (
        <div className="modal-backdrop fade show" onClick={closeDetails}></div>
      )}
    </div>
  );
};

export default DocumentationPage; 