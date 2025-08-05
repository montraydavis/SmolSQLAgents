import React from 'react';
import DocumentationExplorer from '../documentation-explorer/DocumentationExplorer';

const DocumentationSidebar = ({
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
  refreshDocumentation,
  onItemSelect
}) => {
  return (
    <div className="col-md-3">
      <div className="card h-100">
        <div className="card-header bg-white d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Documentation Explorer</h5>
          <div>
            <button
              className="btn btn-sm btn-outline-secondary"
              title="Refresh"
              onClick={refreshDocumentation}
              disabled={documentationData.isLoading}
            >
              <i className={`bi bi-arrow-clockwise ${documentationData.isLoading ? 'spinner-border spinner-border-sm' : ''}`}></i>
            </button>
          </div>
        </div>
        <div className="card-body p-0">
          <DocumentationExplorer
            documentationData={documentationData}
            setDocumentationData={setDocumentationData}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            searchResults={searchResults}
            setSearchResults={setSearchResults}
            isSearching={isSearching}
            setIsSearching={setIsSearching}
            onRefresh={refreshDocumentation}
            onItemSelect={onItemSelect}
          />
        </div>
      </div>
    </div>
  );
};

export default DocumentationSidebar; 