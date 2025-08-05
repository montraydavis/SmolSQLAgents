import React, { useState } from 'react';
import './DocumentationExplorer.css';

const DocumentationExplorer = ({
  documentationData,
  setDocumentationData,
  searchQuery,
  setSearchQuery,
  activeTab,
  setActiveTab,
  searchResults,
  setSearchResults,
  isSearching,
  setIsSearching,
  onRefresh,
  onItemSelect
}) => {
  const [showStatistics, setShowStatistics] = useState(true);
  const [showQuickActions, setShowQuickActions] = useState(true);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await fetch('http://127.0.0.1:5000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          type: 'text'
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.results || []);
      } else {
        console.error('Search failed:', response.statusText);
        setSearchResults([]);
      }
    } catch (error) {
      console.error('Error during search:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleItemSelect = async (item) => {
    try {
      let detailedItem = { ...item };
      
      // Fetch detailed information based on item type
      if (item.type === 'table') {
        // First try to get documentation data
        let hasDocumentationData = false;
        try {
          const response = await fetch(`http://127.0.0.1:5000/api/documentation/tables/${item.name}`);
          if (response.ok) {
            const data = await response.json();
            if (data.success && data.table) {
              detailedItem = {
                ...item,
                table: data.table
              };
              hasDocumentationData = true;
            }
          }
        } catch (error) {
          // Documentation endpoint failed, will fall back to schema endpoint
        }
        
        // Always fetch schema data as fallback or supplement
        if (!hasDocumentationData || !detailedItem.table.schema_data || Object.keys(detailedItem.table.schema_data).length === 0) {
          const schemaResponse = await fetch('http://127.0.0.1:5000/api/schema');
          if (schemaResponse.ok) {
            const schemaData = await schemaResponse.json();
            if (schemaData.success && schemaData.tables) {
              const tableSchema = schemaData.tables.find(t => t.name === item.name);
              if (tableSchema) {
                if (!hasDocumentationData) {
                  // Create a basic table structure if no documentation data exists
                  detailedItem = {
                    ...item,
                    table: {
                      table_name: item.name,
                      name: item.name,
                      business_purpose: '',
                      documentation: '',
                      schema_data: tableSchema,
                      schema: tableSchema,
                      columns: tableSchema.columns || []
                    }
                  };
                } else {
                  // Supplement existing documentation data with schema
                  detailedItem.table = {
                    ...detailedItem.table,
                    schema_data: tableSchema,
                    schema: tableSchema,
                    columns: tableSchema.columns || []
                  };
                }
              }
            }
          }
        }
      } else if (item.type === 'relationship') {
        const relationshipId = item.id.replace('relationship_', '');
        const response = await fetch(`http://127.0.0.1:5000/api/documentation/relationships/${relationshipId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.relationship) {
            detailedItem = {
              ...item,
              relationship: data.relationship
            };
          }
        }
      }
      
      onItemSelect(detailedItem);
    } catch (error) {
      console.error('Error fetching detailed item information:', error);
      // Fallback to basic item
      onItemSelect(item);
    }
  };

  const toggleFolder = (folderName) => {
    const newExpanded = new Set(documentationData.expandedFolders);
    if (newExpanded.has(folderName)) {
      newExpanded.delete(folderName);
    } else {
      newExpanded.add(folderName);
    }
    setDocumentationData(prev => ({
      ...prev,
      expandedFolders: newExpanded
    }));
  };

  const refreshDocumentation = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  // Calculate statistics
  const totalTables = documentationData.tables.length;
  const totalRelationships = documentationData.relationships.length;
  const tablesWithDocumentation = documentationData.tables.filter(t => t.business_purpose).length;
  const relationshipsWithDocumentation = documentationData.relationships.filter(r => r.documentation).length;
  const totalColumns = documentationData.tables.reduce((sum, table) => sum + (table.columns?.length || 0), 0);

  return (
    <div className="documentation-explorer">
      {/* Header */}
      <div className="explorer-header p-3 border-bottom">
        <div className="d-flex justify-content-between align-items-center">
          <h6 className="mb-0 fw-bold">
            <i className="bi bi-journal-text me-2"></i>
            Documentation Explorer
          </h6>
          <button
            className="btn btn-sm btn-outline-secondary"
            onClick={refreshDocumentation}
            title="Refresh documentation"
          >
            <i className="bi bi-arrow-clockwise"></i>
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="search-container p-3 border-bottom">
        <div className="input-group">
          <input
            type="text"
            className="form-control"
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={handleSearchKeyPress} />
          <button
            className="btn btn-outline-secondary"
            type="button"
            onClick={handleSearch}
            disabled={isSearching}
          >
            {isSearching ? (
              <i className="bi bi-arrow-clockwise spinner-border spinner-border-sm"></i>
            ) : (
              <i className="bi bi-search"></i>
            )}
          </button>
        </div>
      </div>

      {/* Statistics Panel */}
      {showStatistics && (
        <div className="statistics-panel p-3 border-bottom">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h6 className="mb-0 fw-bold">
              <i className="bi bi-graph-up me-1"></i>
              Overview
            </h6>
            <button
              className="btn btn-sm btn-outline-secondary"
              onClick={() => setShowStatistics(!showStatistics)}
            >
              <i className={`bi ${showStatistics ? 'bi-chevron-up' : 'bi-chevron-down'}`}></i>
            </button>
          </div>
          <div className="row g-2">
            <div className="col-6">
              <div className="stat-item">
                <div className="stat-number">{totalTables}</div>
                <div className="stat-label">Tables</div>
              </div>
            </div>
            <div className="col-6">
              <div className="stat-item">
                <div className="stat-number">{totalRelationships}</div>
                <div className="stat-label">Relationships</div>
              </div>
            </div>
            <div className="col-6">
              <div className="stat-item">
                <div className="stat-number">{totalColumns}</div>
                <div className="stat-label">Columns</div>
              </div>
            </div>
            <div className="col-6">
              <div className="stat-item">
                <div className="stat-number">{tablesWithDocumentation}</div>
                <div className="stat-label">Documented</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="search-results p-3 border-bottom">
          <h6 className="mb-2">
            <i className="bi bi-search me-1"></i>
            Search Results ({searchResults.length})
          </h6>
          {searchResults.map((result, index) => (
            <div
              key={index}
              className="list-group-item py-1 px-3 border-0"
              style={{ cursor: 'pointer' }}
              onClick={() => handleItemSelect(result)}
            >
              <div className="d-flex align-items-center">
                <i className="bi bi-file-text me-2 text-muted"></i>
                <div className="flex-grow-1">
                  <span className="small fw-medium">{result.name || result.table_name}</span>
                  <div className="small text-muted">{result.description || result.business_purpose}</div>
                </div>
                <span className="badge bg-primary">{result.score?.toFixed(2) || 'N/A'}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Documentation Tree */}
      <div className="documentation-tree">
        {/* Tables Section */}
        <div className="folder-section">
          <div
            className="list-group-item py-2"
            style={{ cursor: 'pointer' }}
            onClick={() => toggleFolder('tables')}
          >
            <div className="d-flex justify-content-between align-items-center">
              <span>
                <i className={`bi ${documentationData.expandedFolders.has('tables') ? 'bi-folder-fill' : 'bi-folder'} me-2`}></i>
                Tables
              </span>
              <span className="badge bg-light text-dark">{documentationData.tables.length}</span>
            </div>
          </div>
          
          {documentationData.expandedFolders.has('tables') && (
            <div className="folder-content">
              {documentationData.tables.length > 0 ? (
                documentationData.tables.map((table, index) => {
                  return (
                    <div
                      key={table.name || `table-${index}`}
                      className="list-group-item py-1 px-3 border-0"
                      style={{ cursor: 'pointer' }}
                      onClick={() => handleItemSelect({
                        id: `table-${table.name || index}`,
                        name: table.name || `Table ${index + 1}`,
                        type: 'table',
                        description: table.business_purpose || `Table containing ${table.columns?.length || 0} columns`,
                        table: table
                      })}
                    >
                      <div className="d-flex align-items-center">
                        <i className="bi bi-table me-2 text-muted"></i>
                        <div className="flex-grow-1">
                          <span className="small fw-medium">
                            {table.name || `Table ${index + 1}`}
                          </span>
                          {table.business_purpose && (
                            <div className="small text-muted" style={{ fontSize: '0.75rem', lineHeight: '1.2' }}>
                              {table.business_purpose.length > 60 
                                ? `${table.business_purpose.substring(0, 60)}...` 
                                : table.business_purpose}
                            </div>
                          )}
                          {!table.business_purpose && table.columns && (
                            <div className="small text-muted">
                              {table.columns.length} columns
                            </div>
                          )}
                        </div>
                        <div className="text-end">
                          {table.column_count && (
                            <span className="badge bg-secondary me-1">{table.column_count}</span>
                          )}
                          {table.primary_key_columns && table.primary_key_columns.length > 0 && (
                            <span className="badge bg-warning me-1">PK</span>
                          )}
                          {table.foreign_key_columns && table.foreign_key_columns.length > 0 && (
                            <span className="badge bg-info me-1">FK</span>
                          )}
                          {table.not_null_columns && table.not_null_columns.length > 0 && (
                            <span className="badge bg-success">NN</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-muted small px-3 py-1">
                  <i className="bi bi-info-circle me-1"></i>
                  No tables found
                </div>
              )}
            </div>
          )}
        </div>

        {/* Relationships Section */}
        <div className="folder-section">
          <div
            className="list-group-item py-2"
            style={{ cursor: 'pointer' }}
            onClick={() => toggleFolder('relationships')}
          >
            <div className="d-flex justify-content-between align-items-center">
              <span>
                <i className={`bi ${documentationData.expandedFolders.has('relationships') ? 'bi-folder-fill' : 'bi-folder'} me-2`}></i>
                Relationships
              </span>
              <span className="badge bg-light text-dark">{documentationData.relationships.length}</span>
            </div>
          </div>
          
          {documentationData.expandedFolders.has('relationships') && (
            <div className="folder-content">
              {documentationData.relationships.length > 0 ? (
                documentationData.relationships.map((relationship, index) => (
                  <div
                    key={relationship.id || `relationship-${index}`}
                    className="list-group-item py-1 px-3 border-0"
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleItemSelect({
                      id: `relationship-${relationship.id || index}`,
                      name: `${relationship.constrained_table} → ${relationship.referred_table}`,
                      type: 'relationship',
                      description: relationship.relationship_type || 'Relationship',
                      relationship: relationship
                    })}
                  >
                    <div className="d-flex align-items-center">
                      <i className="bi bi-arrow-right me-2 text-muted"></i>
                      <div className="flex-grow-1">
                        <span className="small fw-medium">
                          {relationship.constrained_table} → {relationship.referred_table}
                        </span>
                        <div className="small text-muted">
                          {relationship.relationship_type || 'Relationship'}
                          {relationship.documentation && (
                            <span className="ms-2" style={{ fontSize: '0.75rem' }}>
                              • {relationship.documentation.length > 40 
                                ? `${relationship.documentation.substring(0, 40)}...` 
                                : relationship.documentation}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-muted small px-3 py-1">
                  <i className="bi bi-info-circle me-1"></i>
                  No relationships found
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions Panel */}
      {showQuickActions && (
        <div className="quick-actions-panel p-3 border-top">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h6 className="mb-0 fw-bold">
              <i className="bi bi-lightning me-1"></i>
              Quick Actions
            </h6>
            <button
              className="btn btn-sm btn-outline-secondary"
              onClick={() => setShowQuickActions(!showQuickActions)}
            >
              <i className={`bi ${showQuickActions ? 'bi-chevron-down' : 'bi-chevron-up'}`}></i>
            </button>
          </div>
          <div className="d-grid gap-2">
            <button className="btn btn-sm btn-outline-primary">
              <i className="bi bi-plus-circle me-1"></i>
              Add Documentation
            </button>
            <button className="btn btn-sm btn-outline-secondary">
              <i className="bi bi-download me-1"></i>
              Export Schema
            </button>
            <button className="btn btn-sm btn-outline-info">
              <i className="bi bi-question-circle me-1"></i>
              Help
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentationExplorer; 