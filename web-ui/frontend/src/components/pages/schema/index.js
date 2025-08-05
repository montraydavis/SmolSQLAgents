import React, { useState, useEffect } from 'react';
import './SchemaPage.css';

const SchemaPage = () => {
  const [schemaData, setSchemaData] = useState({
    tables: [],
    relationships: [],
    statistics: {
      totalTables: 0,
      totalColumns: 0,
      totalRelationships: 0,
      dataTypes: {},
      constraints: {}
    }
  });
  const [filteredTables, setFilteredTables] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTable, setSelectedTable] = useState(null);
  const [showTableDetails, setShowTableDetails] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMode, setViewMode] = useState('cards'); // 'cards' or 'table'
  const [sortBy, setSortBy] = useState('name'); // 'name', 'columns', 'relationships'

  useEffect(() => {
    loadSchemaData();
  }, []);

  useEffect(() => {
    filterAndSortTables();
  }, [schemaData, searchQuery, sortBy]);

  const loadSchemaData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:5000/api/schema');
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          const tables = data.tables || [];
          const relationships = data.relationships || [];
          
          // Calculate statistics
          const statistics = calculateStatistics(tables, relationships);
          
          setSchemaData({
            tables,
            relationships,
            statistics
          });
        }
      }
    } catch (error) {
      console.error('Error loading schema data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const calculateStatistics = (tables, relationships) => {
    const dataTypes = {};
    const constraints = {
      primaryKeys: 0,
      foreignKeys: 0,
      uniqueConstraints: 0,
      notNullColumns: 0
    };

    let totalColumns = 0;

    tables.forEach(table => {
      if (table.columns) {
        totalColumns += table.columns.length;
        
        table.columns.forEach(column => {
          // Count data types
          const type = column.type?.split('(')[0] || 'UNKNOWN';
          dataTypes[type] = (dataTypes[type] || 0) + 1;
          
          // Count constraints
          if (column.primary_key) constraints.primaryKeys++;
          if (column.foreign_key) constraints.foreignKeys++;
          if (column.unique) constraints.uniqueConstraints++;
          if (!column.nullable) constraints.notNullColumns++;
        });
      }
    });

    return {
      totalTables: tables.length,
      totalColumns,
      totalRelationships: relationships.length,
      dataTypes,
      constraints
    };
  };

  const filterAndSortTables = () => {
    let filtered = schemaData.tables;

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(table => 
        table.name?.toLowerCase().includes(query) ||
        table.columns?.some(col => col.name?.toLowerCase().includes(query)) ||
        table.columns?.some(col => col.type?.toLowerCase().includes(query))
      );
    }

    // Sort tables
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return (a.name || '').localeCompare(b.name || '');
        case 'columns':
          return (b.columns?.length || 0) - (a.columns?.length || 0);
        case 'relationships':
          const aRels = schemaData.relationships.filter(r => 
            r.constrained_table === a.name || r.referred_table === a.name
          ).length;
          const bRels = schemaData.relationships.filter(r => 
            r.constrained_table === b.name || r.referred_table === b.name
          ).length;
          return bRels - aRels;
        default:
          return 0;
      }
    });

    setFilteredTables(filtered);
  };

  const handleTableClick = async (table) => {
    setSelectedTable(table);
    setShowTableDetails(true);
    
    // Fetch documentation data for this table
    try {
      const docResponse = await fetch(`http://127.0.0.1:5000/api/documentation/tables/${table.name}`);
      if (docResponse.ok) {
        const docData = await docResponse.json();
        if (docData.success) {
          setSelectedTable({
            ...table,
            documentation: docData.documentation,
            business_purpose: docData.business_purpose,
            status: docData.status,
            processed_at: docData.processed_at
          });
        }
      }
    } catch (error) {
      console.error('Error fetching documentation:', error);
    }
  };

  const closeTableDetails = () => {
    setShowTableDetails(false);
    setSelectedTable(null);
  };

  const getTableRelationships = (tableName) => {
    return schemaData.relationships.filter(rel => 
      rel.constrained_table === tableName || rel.referred_table === tableName
    );
  };

  const getDataTypeColor = (type) => {
    const typeMap = {
      'INTEGER': 'primary',
      'VARCHAR': 'info',
      'DECIMAL': 'success',
      'DATETIME': 'warning',
      'DATE': 'secondary',
      'BOOLEAN': 'dark'
    };
    return typeMap[type] || 'secondary';
  };

  const getConstraintBadges = (column) => {
    const badges = [];
    if (column.primary_key) badges.push({ text: 'PK', color: 'warning' });
    if (column.foreign_key) badges.push({ text: 'FK', color: 'info' });
    if (column.unique) badges.push({ text: 'UQ', color: 'success' });
    if (!column.nullable) badges.push({ text: 'NN', color: 'danger' });
    return badges;
  };

  if (isLoading) {
    return (
      <div className="schema-page">
        <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="schema-page">
      {/* Header */}
      <div className="page-header">
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <h2 className="mb-1">
              <i className="bi bi-diagram-3 me-2"></i>
              Database Schema
            </h2>
            <p className="text-muted mb-0">
              {schemaData.statistics.totalTables} tables, {schemaData.statistics.totalColumns} columns, {schemaData.statistics.totalRelationships} relationships
            </p>
          </div>
          <button 
            className="btn btn-outline-primary"
            onClick={loadSchemaData}
          >
            <i className="bi bi-arrow-clockwise me-1"></i>
            Refresh
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="statistics-section">
        <div className="row g-3">
          <div className="col-md-3">
            <div className="stat-card">
              <div className="stat-icon bg-primary">
                <i className="bi bi-table"></i>
              </div>
              <div className="stat-content">
                <h3>{schemaData.statistics.totalTables}</h3>
                <p>Tables</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="stat-card">
              <div className="stat-icon bg-info">
                <i className="bi bi-list-ul"></i>
              </div>
              <div className="stat-content">
                <h3>{schemaData.statistics.totalColumns}</h3>
                <p>Columns</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="stat-card">
              <div className="stat-icon bg-success">
                <i className="bi bi-arrow-right"></i>
              </div>
              <div className="stat-content">
                <h3>{schemaData.statistics.totalRelationships}</h3>
                <p>Relationships</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="stat-card">
              <div className="stat-icon bg-warning">
                <i className="bi bi-key"></i>
              </div>
              <div className="stat-content">
                <h3>{schemaData.statistics.constraints.primaryKeys}</h3>
                <p>Primary Keys</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Controls */}
      <div className="controls-section">
        <div className="row g-3">
          <div className="col-md-6">
            <div className="input-group">
              <span className="input-group-text">
                <i className="bi bi-search"></i>
              </span>
              <input
                type="text"
                className="form-control"
                placeholder="Search tables, columns, or data types..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
          <div className="col-md-3">
            <select
              className="form-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="name">Sort by Name</option>
              <option value="columns">Sort by Column Count</option>
              <option value="relationships">Sort by Relationships</option>
            </select>
          </div>
          <div className="col-md-3">
            <div className="btn-group w-100" role="group">
              <button
                type="button"
                className={`btn btn-outline-secondary ${viewMode === 'cards' ? 'active' : ''}`}
                onClick={() => setViewMode('cards')}
              >
                <i className="bi bi-grid-3x3-gap"></i>
              </button>
              <button
                type="button"
                className={`btn btn-outline-secondary ${viewMode === 'table' ? 'active' : ''}`}
                onClick={() => setViewMode('table')}
              >
                <i className="bi bi-table"></i>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Schema Content */}
      <div className="schema-content">
        {viewMode === 'cards' ? (
          <div className="cards-view">
            {filteredTables.length > 0 ? (
              <div className="row g-4">
                {filteredTables.map((table, index) => (
                  <div key={index} className="col-lg-6 col-xl-4">
                    <div 
                      className="schema-card"
                      onClick={() => handleTableClick(table)}
                    >
                      <div className="card h-100">
                        <div className="card-header d-flex justify-content-between align-items-center">
                          <span className="badge bg-primary">
                            <i className="bi bi-table me-1"></i>
                            Table
                          </span>
                          <div className="table-stats">
                            <small className="text-muted">
                              {table.columns?.length || 0} columns
                            </small>
                          </div>
                        </div>
                        <div className="card-body">
                          <h6 className="card-title">{table.name}</h6>
                          
                          {/* Column Preview */}
                          <div className="columns-preview">
                            {table.columns?.slice(0, 3).map((col, colIndex) => (
                              <div key={colIndex} className="column-item">
                                <code className="column-name">{col.name}</code>
                                <span className={`badge bg-${getDataTypeColor(col.type)}`}>
                                  {col.type?.split('(')[0]}
                                </span>
                                {getConstraintBadges(col).map((badge, badgeIndex) => (
                                  <span key={badgeIndex} className={`badge bg-${badge.color}`}>
                                    {badge.text}
                                  </span>
                                ))}
                              </div>
                            ))}
                            {table.columns?.length > 3 && (
                              <div className="more-columns">
                                <small className="text-muted">
                                  +{table.columns.length - 3} more columns
                                </small>
                              </div>
                            )}
                          </div>

                          {/* Relationships */}
                          {getTableRelationships(table.name).length > 0 && (
                            <div className="relationships-preview mt-2">
                              <small className="text-muted">
                                {getTableRelationships(table.name).length} relationships
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
                    {searchQuery 
                      ? 'Try adjusting your search criteria.'
                      : 'No tables are currently available in the database.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="table-view">
            <div className="table-responsive">
              <table className="table table-hover">
                <thead>
                  <tr>
                    <th>Table Name</th>
                    <th>Columns</th>
                    <th>Primary Keys</th>
                    <th>Foreign Keys</th>
                    <th>Relationships</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTables.map((table, index) => (
                    <tr key={index}>
                      <td>
                        <strong>{table.name}</strong>
                      </td>
                      <td>
                        <span className="badge bg-secondary">
                          {table.columns?.length || 0}
                        </span>
                      </td>
                      <td>
                        {table.columns?.filter(col => col.primary_key).length || 0}
                      </td>
                      <td>
                        {table.columns?.filter(col => col.foreign_key).length || 0}
                      </td>
                      <td>
                        <span className="badge bg-info">
                          {getTableRelationships(table.name).length}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => handleTableClick(table)}
                        >
                          <i className="bi bi-eye"></i>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Table Details Modal */}
      {showTableDetails && selectedTable && (
        <div className="modal fade show" style={{ display: 'block' }} tabIndex="-1">
          <div className="modal-dialog modal-xl">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-table me-2"></i>
                  {selectedTable.name}
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={closeTableDetails}
                  aria-label="Close"
                ></button>
              </div>
              <div className="modal-body">
                <div className="row">
                  <div className="col-md-8">
                    {/* Documentation Section */}
                    {(selectedTable.business_purpose || selectedTable.documentation) && (
                      <>
                        <h6>Documentation</h6>
                        {selectedTable.business_purpose && (
                          <div className="mb-3">
                            <strong>Business Purpose:</strong>
                            <p className="text-muted mb-0 mt-1">
                              {selectedTable.business_purpose}
                            </p>
                          </div>
                        )}
                        {selectedTable.documentation && (
                          <div className="mb-4">
                            <strong>Detailed Documentation:</strong>
                            <div className="bg-light p-3 rounded mt-1">
                              <p className="mb-0">
                                {selectedTable.documentation}
                              </p>
                            </div>
                          </div>
                        )}
                      </>
                    )}

                    <h6>Schema Information</h6>
                    <div className="table-responsive">
                      <table className="table table-sm">
                        <thead>
                          <tr>
                            <th>Column</th>
                            <th>Data Type</th>
                            <th>Nullable</th>
                            <th>Default</th>
                            <th>Constraints</th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedTable.columns?.map((column, index) => (
                            <tr key={index}>
                              <td>
                                <code>{column.name}</code>
                              </td>
                              <td>
                                <span className={`badge bg-${getDataTypeColor(column.type)}`}>
                                  {column.type}
                                </span>
                              </td>
                              <td>
                                <span className={`badge ${column.nullable ? 'bg-success' : 'bg-danger'}`}>
                                  {column.nullable ? 'NULL' : 'NOT NULL'}
                                </span>
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
                                  {getConstraintBadges(column).map((badge, badgeIndex) => (
                                    <span key={badgeIndex} className={`badge bg-${badge.color}`}>
                                      {badge.text}
                                    </span>
                                  ))}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <h6>Table Statistics</h6>
                    <ul className="list-unstyled">
                      <li><strong>Total Columns:</strong> {selectedTable.columns?.length || 0}</li>
                      <li><strong>Primary Keys:</strong> {selectedTable.columns?.filter(col => col.primary_key).length || 0}</li>
                      <li><strong>Foreign Keys:</strong> {selectedTable.columns?.filter(col => col.foreign_key).length || 0}</li>
                      <li><strong>Nullable Columns:</strong> {selectedTable.columns?.filter(col => col.nullable).length || 0}</li>
                      <li><strong>Not Null Columns:</strong> {selectedTable.columns?.filter(col => !col.nullable).length || 0}</li>
                    </ul>

                    {/* Documentation Status */}
                    {selectedTable.status && (
                      <>
                        <h6 className="mt-4">Documentation Status</h6>
                        <ul className="list-unstyled">
                          <li>
                            <strong>Status:</strong> 
                            <span className={`badge ms-2 ${selectedTable.status === 'completed' ? 'bg-success' : selectedTable.status === 'pending' ? 'bg-warning' : 'bg-danger'}`}>
                              {selectedTable.status}
                            </span>
                          </li>
                          {selectedTable.processed_at && (
                            <li><strong>Processed:</strong> {new Date(selectedTable.processed_at).toLocaleString()}</li>
                          )}
                          <li><strong>Has Business Purpose:</strong> {selectedTable.business_purpose ? 'Yes' : 'No'}</li>
                          <li><strong>Has Documentation:</strong> {selectedTable.documentation ? 'Yes' : 'No'}</li>
                        </ul>
                      </>
                    )}

                    <h6 className="mt-4">Relationships</h6>
                    {getTableRelationships(selectedTable.name).length > 0 ? (
                      <div className="relationships-list">
                        {getTableRelationships(selectedTable.name).map((rel, index) => (
                          <div key={index} className="relationship-item">
                            <small>
                              <strong>{rel.constrained_table}</strong> → <strong>{rel.referred_table}</strong>
                            </small>
                            <br />
                            <small className="text-muted">
                              {rel.constrained_columns?.join(', ')} → {rel.referred_columns?.join(', ')}
                            </small>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-muted small">No relationships found</p>
                    )}
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={closeTableDetails}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Modal Backdrop */}
      {showTableDetails && (
        <div className="modal-backdrop fade show" onClick={closeTableDetails}></div>
      )}
    </div>
  );
};

export default SchemaPage; 