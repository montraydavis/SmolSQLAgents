import React, { useState, useEffect } from 'react';
import './RelationshipsPage.css';

const RelationshipsPage = () => {
  const [relationships, setRelationships] = useState([]);
  const [filteredRelationships, setFilteredRelationships] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRelationship, setSelectedRelationship] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    loadRelationships();
  }, []);

  useEffect(() => {
    filterRelationships();
  }, [relationships, searchQuery, selectedType]);

  const loadRelationships = async () => {
    setIsLoading(true);
    try {
      // Try to get relationships from documentation endpoint first
      const response = await fetch('http://127.0.0.1:5000/api/documentation/relationships');
      let relationshipsData = [];
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.relationships) {
          relationshipsData = Object.values(data.relationships);
        }
      }
      
      // If no documentation relationships, get from schema endpoint
      if (relationshipsData.length === 0) {
        const schemaResponse = await fetch('http://127.0.0.1:5000/api/schema');
        if (schemaResponse.ok) {
          const schemaData = await schemaResponse.json();
          if (schemaData.success && schemaData.relationships) {
            relationshipsData = schemaData.relationships.map(rel => ({
              id: `${rel.constrained_table}_${rel.referred_table}`,
              constrained_table: rel.constrained_table,
              referred_table: rel.referred_table,
              constrained_columns: rel.constrained_columns,
              referred_columns: rel.referred_columns,
              relationship_type: 'Foreign Key',
              documentation: `Foreign key relationship from ${rel.constrained_table} to ${rel.referred_table}`
            }));
          }
        }
      }
      
      setRelationships(relationshipsData);
    } catch (error) {
      console.error('Error loading relationships:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterRelationships = () => {
    let filtered = relationships;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(rel => 
        rel.constrained_table.toLowerCase().includes(query) ||
        rel.referred_table.toLowerCase().includes(query) ||
        rel.relationship_type?.toLowerCase().includes(query) ||
        rel.documentation?.toLowerCase().includes(query)
      );
    }

    // Filter by type
    if (selectedType !== 'all') {
      filtered = filtered.filter(rel => rel.relationship_type === selectedType);
    }

    setFilteredRelationships(filtered);
  };

  const getRelationshipTypeColor = (type) => {
    switch (type?.toLowerCase()) {
      case 'one-to-many':
        return 'primary';
      case 'many-to-one':
        return 'info';
      case 'one-to-one':
        return 'success';
      case 'many-to-many':
        return 'warning';
      case 'foreign key':
        return 'secondary';
      default:
        return 'dark';
    }
  };

  const handleRelationshipClick = (relationship) => {
    setSelectedRelationship(relationship);
    setShowDetails(true);
  };

  const closeDetails = () => {
    setShowDetails(false);
    setSelectedRelationship(null);
  };

  const getUniqueTypes = () => {
    const types = relationships.map(rel => rel.relationship_type).filter(Boolean);
    return ['all', ...new Set(types)];
  };

  if (isLoading) {
    return (
      <div className="relationships-page">
        <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relationships-page">
      {/* Header */}
      <div className="page-header">
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <h2 className="mb-1">
              <i className="bi bi-arrow-left-right me-2"></i>
              Database Relationships
            </h2>
            <p className="text-muted mb-0">
              {filteredRelationships.length} of {relationships.length} relationships
            </p>
          </div>
          <button 
            className="btn btn-outline-primary"
            onClick={loadRelationships}
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
                placeholder="Search relationships..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
          <div className="col-md-3">
            <select
              className="form-select"
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
            >
              {getUniqueTypes().map(type => (
                <option key={type} value={type}>
                  {type === 'all' ? 'All Types' : type}
                </option>
              ))}
            </select>
          </div>
          <div className="col-md-3">
            <button 
              className="btn btn-outline-secondary w-100"
              onClick={() => {
                setSearchQuery('');
                setSelectedType('all');
              }}
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Relationships Grid */}
      <div className="relationships-grid">
        {filteredRelationships.length > 0 ? (
          <div className="row g-4">
            {filteredRelationships.map((relationship, index) => (
              <div key={relationship.id || index} className="col-lg-6 col-xl-4">
                <div 
                  className="relationship-card"
                  onClick={() => handleRelationshipClick(relationship)}
                >
                  <div className="card h-100">
                    <div className="card-header d-flex justify-content-between align-items-center">
                      <span className="badge bg-primary">
                        {relationship.relationship_type || 'Foreign Key'}
                      </span>
                      <i className="bi bi-arrow-right text-muted"></i>
                    </div>
                    <div className="card-body">
                      <div className="relationship-flow">
                        <div className="table-info">
                          <h6 className="mb-1">{relationship.constrained_table}</h6>
                          <small className="text-muted">
                            {relationship.constrained_columns?.join(', ') || 'N/A'}
                          </small>
                        </div>
                        <div className="arrow-container">
                          <i className="bi bi-arrow-right"></i>
                        </div>
                        <div className="table-info">
                          <h6 className="mb-1">{relationship.referred_table}</h6>
                          <small className="text-muted">
                            {relationship.referred_columns?.join(', ') || 'N/A'}
                          </small>
                        </div>
                      </div>
                      {relationship.documentation && (
                        <div className="mt-3">
                          <small className="text-muted">
                            {relationship.documentation.length > 100 
                              ? `${relationship.documentation.substring(0, 100)}...`
                              : relationship.documentation}
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
              <i className="bi bi-arrow-left-right display-1 text-muted"></i>
              <h4 className="mt-3">No relationships found</h4>
              <p className="text-muted">
                {searchQuery || selectedType !== 'all' 
                  ? 'Try adjusting your search criteria or filters.'
                  : 'No relationships are currently defined in the database.'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Relationship Details Modal */}
      {showDetails && selectedRelationship && (
        <div className="modal fade show" style={{ display: 'block' }} tabIndex="-1">
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-arrow-right me-2"></i>
                  Relationship Details
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
                  <div className="col-md-6">
                    <h6>Constrained Table</h6>
                    <div className="card">
                      <div className="card-body">
                        <h5 className="card-title">{selectedRelationship.constrained_table}</h5>
                        <p className="card-text">
                          <strong>Columns:</strong> {selectedRelationship.constrained_columns?.join(', ') || 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <h6>Referred Table</h6>
                    <div className="card">
                      <div className="card-body">
                        <h5 className="card-title">{selectedRelationship.referred_table}</h5>
                        <p className="card-text">
                          <strong>Columns:</strong> {selectedRelationship.referred_columns?.join(', ') || 'N/A'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-4">
                  <h6>Relationship Type</h6>
                  <span className={`badge bg-${getRelationshipTypeColor(selectedRelationship.relationship_type)}`}>
                    {selectedRelationship.relationship_type || 'Foreign Key'}
                  </span>
                </div>

                {selectedRelationship.documentation && (
                  <div className="mt-4">
                    <h6>Documentation</h6>
                    <div className="bg-light p-3 rounded">
                      <p className="mb-0">{selectedRelationship.documentation}</p>
                    </div>
                  </div>
                )}
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

export default RelationshipsPage; 