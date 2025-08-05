import React from 'react';

const TopNavigation = ({ currentPage, setCurrentPage }) => {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
      <div className="container-fluid" style={{ color: 'white' }}>
        <i className="bi bi-database-gear me-2"></i>SQL Agent
        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <button
                className={`nav-link ${currentPage === 'query' ? 'active' : ''}`}
                onClick={() => setCurrentPage('query')}
              >
                <i className="bi bi-search me-1"></i>Query
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link ${currentPage === 'schema' ? 'active' : ''}`}
                onClick={() => setCurrentPage('schema')}
              >
                <i className="bi bi-diagram-3 me-1"></i>Schema
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link ${currentPage === 'relationships' ? 'active' : ''}`}
                onClick={() => setCurrentPage('relationships')}
              >
                <i className="bi bi-diagram-3-fill me-1"></i>Relationships
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link ${currentPage === 'documentation' ? 'active' : ''}`}
                onClick={() => setCurrentPage('documentation')}
              >
                <i className="bi bi-journal-text me-1"></i>Documentation
              </button>
            </li>
          </ul>
          <div className="d-flex">
            <button className="btn btn-outline-light me-2" id="connectBtn">
              <i className="bi bi-plug-fill me-1"></i> Connect to Database
            </button>
            <div className="dropdown">
              <button className="btn btn-light dropdown-toggle" type="button" id="userMenu" data-bs-toggle="dropdown">
                <i className="bi bi-person-circle me-1"></i> User
              </button>
              <ul className="dropdown-menu dropdown-menu-end">
                <li><button className="dropdown-item">Profile</button></li>
                <li><button className="dropdown-item">Settings</button></li>
                <li><hr className="dropdown-divider" /></li>
                <li><button className="dropdown-item">Logout</button></li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default TopNavigation; 