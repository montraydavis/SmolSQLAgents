import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import DocumentationExplorer from './components/documentation-explorer/DocumentationExplorer';
import RelationshipsPage from './components/pages/relationships';
import DocumentationPage from './components/pages/documentation';
import SchemaPage from './components/pages/schema';
import {
  SplashScreen,
  TopNavigation,
  DocumentationSidebar,
  QueryPage,
  ItemDetailsModal
} from './components';

function App() {
  const [message, setMessage] = useState('');
  const [query, setQuery] = useState('');
  const [generatedSql, setGeneratedSql] = useState('-- Your generated SQL will appear here');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('text-search');
  const [searchQuery, setSearchQuery] = useState('');

  // New state for comprehensive SQL Agent results
  const [sqlAgentStatus, setSqlAgentStatus] = useState(null);
  const [pipelineResults, setPipelineResults] = useState(null);
  const [entityRecognition, setEntityRecognition] = useState(null);
  const [businessContext, setBusinessContext] = useState(null);
  const [sqlValidation, setSqlValidation] = useState(null);
  const [optimizationSuggestions, setOptimizationSuggestions] = useState([]);
  const [queryExecution, setQueryExecution] = useState(null);

  // Splash screen state
  const [showSplash, setShowSplash] = useState(true);
  const [splashStatus, setSplashStatus] = useState('checking');
  const [splashMessage, setSplashMessage] = useState('Initializing SQL Agents...');
  const [splashProgress, setSplashProgress] = useState(0);
  const [pollingAttempts, setPollingAttempts] = useState(0);

  // Documentation explorer state
  const [documentationData, setDocumentationData] = useState({
    tables: [],
    relationships: [],
    searchResults: [],
    expandedFolders: new Set(['tables', 'relationships']),
    isLoading: false
  });
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [currentPage, setCurrentPage] = useState('query'); // Add navigation state

  // Modal state for item details
  const [showItemDetails, setShowItemDetails] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  const initializeApp = useCallback(async () => {
    setSplashStatus('checking');
    setSplashMessage('Checking SQL Agent availability...');
    setSplashProgress(20);

    // Start polling for connection
    const pollForConnection = async () => {
      let attempts = 0;
      const maxAttempts = 30; // 30 seconds max
      const pollInterval = 1000; // 1 second intervals

      while (attempts < maxAttempts) {
        setPollingAttempts(attempts + 1);

        try {
          const response = await fetch('http://127.0.0.1:5000/api/status');
          if (response.ok) {
            const status = await response.json();
            setSqlAgentStatus(status);
            setSplashProgress(50);
            setSplashMessage('SQL Agent status received...');

            // Check if SQL Agents are available and initialized
            if (status.sql_agents_available && status.initialized) {
              setSplashProgress(80);
              setSplashMessage('SQL Agents ready! Loading application...');

              // Simulate loading time for better UX
              await new Promise(resolve => setTimeout(resolve, 1000));

              setSplashProgress(100);
              setSplashMessage('Application ready!');

              // Hide splash screen
              setTimeout(() => {
                setShowSplash(false);
              }, 500);
              return; // Success - exit polling
            } else {
              setSplashMessage(`SQL Agents not ready (attempt ${attempts + 1}/${maxAttempts})...`);
            }
          } else {
            setSplashMessage(`Backend responding but not ready (attempt ${attempts + 1}/${maxAttempts})...`);
          }
        } catch (error) {
          console.error(`Connection attempt ${attempts + 1} failed:`, error);
          setSplashMessage(`Connecting to backend... (attempt ${attempts + 1}/${maxAttempts})`);
        }

        attempts++;
        setSplashProgress(20 + (attempts / maxAttempts) * 30); // Progress from 20% to 50%

        // Wait before next attempt
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }

      // If we get here, max attempts reached
      setSplashStatus('error');
      setSplashMessage('Cannot connect to backend server after multiple attempts');
      setSplashProgress(100);
    };

    // Start polling
    pollForConnection();
  }, []);

  const loadDocumentationData = useCallback(async () => {
    setDocumentationData(prev => ({ ...prev, isLoading: true }));
    try {
      console.log('Loading documentation data...');

      // Load summaries first
      const summariesResponse = await fetch('http://127.0.0.1:5000/api/documentation/summaries');
      let hasSummaries = false;

      if (summariesResponse.ok) {
        const summariesData = await summariesResponse.json();
        console.log('Summaries API response:', summariesData);
        if (summariesData.success && summariesData.summaries && Object.keys(summariesData.summaries).length > 0) {
          // Extract tables and relationships from summaries
          const tables = [];
          const relationships = [];

          Object.values(summariesData.summaries).forEach(item => {
            if (item.type === 'table') {
              tables.push({
                name: item.name,
                business_purpose: item.business_purpose,
                documentation: item.documentation,
                status: item.status
              });
            } else if (item.type === 'relationship') {
              relationships.push({
                id: item.id.replace('relationship_', ''),
                constrained_table: item.constrained_table,
                referred_table: item.referred_table,
                relationship_type: item.relationship_type,
                documentation: item.documentation,
                status: item.status
              });
            }
          });

          if (tables.length > 0 || relationships.length > 0) {
            hasSummaries = true;
            setDocumentationData(prev => ({
              ...prev,
              tables: tables,
              relationships: relationships,
              isLoading: false
            }));
          }
        }
      }

      // If no summaries or summaries are empty, fallback to schema endpoint
      if (!hasSummaries) {
        console.log('No summaries available, falling back to schema endpoint...');
        const schemaResponse = await fetch('http://127.0.0.1:5000/api/schema');
        if (schemaResponse.ok) {
          const schemaData = await schemaResponse.json();
          console.log('Schema API response:', schemaData);
          if (schemaData.success) {
            console.log('Tables received:', schemaData.tables);
            setDocumentationData(prev => ({
              ...prev,
              tables: schemaData.tables || [],
              isLoading: false
            }));
          } else {
            console.error('Schema API returned error:', schemaData.error);
            setDocumentationData(prev => ({ ...prev, isLoading: false }));
          }
        } else {
          throw new Error(`HTTP ${schemaResponse.status}: ${schemaResponse.statusText}`);
        }

        // Load relationships
        const relationshipsResponse = await fetch('http://127.0.0.1:5000/api/documentation/relationships');
        if (relationshipsResponse.ok) {
          const relationshipsData = await relationshipsResponse.json();
          if (relationshipsData.success) {
            setDocumentationData(prev => ({
              ...prev,
              relationships: relationshipsData.relationships ? Object.values(relationshipsData.relationships) : []
            }));
          }
        }
      }
    } catch (error) {
      console.error('Error loading documentation data:', error);
      setDocumentationData(prev => ({ ...prev, isLoading: false, tables: [] }));
    }
  }, []);

  // Initialize app on mount
  useEffect(() => {
    initializeApp();
  }, [initializeApp]);

  // Load documentation data when app is ready
  useEffect(() => {
    if (!showSplash && sqlAgentStatus?.sql_agents_available) {
      loadDocumentationData();
    }
  }, [showSplash, sqlAgentStatus, loadDocumentationData]);

  // Remove the keyboard event listener that was interfering with modal handling
  // The DocumentationExplorer component handles its own modal interactions

  const executeQuery = useCallback(async () => {
    console.log('executeQuery called with query:', query);
    if (!query.trim()) return;

    setIsLoading(true);

    // Reset all results
    setPipelineResults(null);
    setEntityRecognition(null);
    setBusinessContext(null);
    setSqlValidation(null);
    setOptimizationSuggestions([]);
    setQueryExecution(null);

    try {
      console.log('Making API call to /api/query with query:', query.trim());
      const response = await fetch('http://127.0.0.1:5000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim() })
      });

      console.log('API response status:', response.status);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      console.log('API Response - data:', data);
      console.log('API Response - data.results:', data.results);
      console.log('API Response - data.pipeline_results:', data.pipeline_results);
      console.log('API Response - data.pipeline_results.sql_generation:', data.pipeline_results?.sql_generation);

      // Always set the SQL and results, regardless of success status
      setGeneratedSql(data.sql);
      
      // Extract results from the correct location in the response
      let extractedResults = data.results;
      if (data.pipeline_results?.sql_generation?.validation?.execution?.sample_data?.sample_rows) {
        extractedResults = data.pipeline_results.sql_generation.validation.execution.sample_data.sample_rows;
      }
      
      setResults(extractedResults);
      
      console.log('Setting results to:', extractedResults);

      // Extract comprehensive pipeline results if available
      if (data.pipeline_results) {
        setPipelineResults(data.pipeline_results);

        // Extract entity recognition results
        const entityRecognition = data.pipeline_results.entity_recognition;
        if (entityRecognition) {
          setEntityRecognition(entityRecognition);
        }

        // Extract business context results
        const businessContext = data.pipeline_results.business_context;
        if (businessContext) {
          setBusinessContext(businessContext);
        }

        // Extract SQL generation results
        const sqlGeneration = data.pipeline_results.sql_generation;
        if (sqlGeneration) {
          setSqlValidation(sqlGeneration.validation);
          setOptimizationSuggestions(sqlGeneration.optimization_suggestions || []);
          
          // Extract query execution data from the correct location
          const queryExecData = sqlGeneration.validation?.execution || sqlGeneration.query_execution;
          setQueryExecution(queryExecData);
        }
      }

      // Show appropriate message based on success status
      if (data.success) {
        console.log('✅ SQL Agent pipeline completed successfully');
        console.log('Pipeline Results:', data.pipeline_results);
      } else {
        console.log('ℹ️ SQL Agent pipeline returned error');
        console.log('Error:', data.error);
      }
    } catch (error) {
      console.error('Error executing query:', error);
      // Set empty results on error
      setGeneratedSql('-- Error: Could not execute query');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, [query, setGeneratedSql, setResults, setPipelineResults, setEntityRecognition, setBusinessContext, setSqlValidation, setOptimizationSuggestions, setQueryExecution, setIsLoading]);

  const copySqlToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generatedSql);
      // You could add a toast notification here
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      executeQuery();
    }
  };

  const refreshDocumentation = () => {
    loadDocumentationData();
  };

  const handleItemSelect = (item) => {
    setSelectedItem(item);
    setShowItemDetails(true);
  };

  const checkSQLAgentStatus = useCallback(async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/status');
      if (response.ok) {
        const status = await response.json();
        setSqlAgentStatus(status);
        console.log('SQL Agent Status:', status);

        // Show status in the UI
        if (status.sql_agents_available) {
          console.log('✅ SQL Agents are available!');
          if (status.initialized) {
            console.log('✅ SQL Agents are initialized!');
            console.log('Features available:', status.features);
            console.log('Agents status:', status.agents);
          } else {
            console.log('⚠️ SQL Agents are available but not initialized');
          }
        } else {
          console.log('❌ SQL Agents are not available');
        }

        return status;
      }
    } catch (error) {
      console.error('Error checking SQL Agent status:', error);
    }
    return null;
  }, []);

  // Check SQL Agent status on mount
  useEffect(() => {
    checkSQLAgentStatus();
  }, [checkSQLAgentStatus]);

  // Debug: Monitor results state changes
  useEffect(() => {
    console.log('App - results state changed:', results);
  }, [results]);

  // Fetch initial message
  useEffect(() => {
    // Fetch the message from the backend API
    fetch('http://127.0.0.1:5000/api/message')
      .then(res => res.json())
      .then(data => setMessage(data.message))
      .catch(err => console.error('Error fetching message:', err));
  }, [setMessage]);

  const retryInitialization = useCallback(() => {
    setShowSplash(true);
    setSplashStatus('checking');
    setSplashProgress(0);
    setPollingAttempts(0);
    setSplashMessage('Retrying connection...');
    initializeApp();
  }, [initializeApp]);



  // Show splash screen if not ready
  if (showSplash) {
    return (
      <SplashScreen
        splashStatus={splashStatus}
        splashMessage={splashMessage}
        splashProgress={splashProgress}
        pollingAttempts={pollingAttempts}
        retryInitialization={retryInitialization}
      />
    );
  }

  // Main application (existing code)
  return (
    <div className="App">
      {/* Top Navigation */}
      <TopNavigation currentPage={currentPage} setCurrentPage={setCurrentPage} />

      <div className="container-fluid mt-3">
        <div className="row g-3">
          {/* Left Sidebar */}
          <DocumentationSidebar
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
            refreshDocumentation={refreshDocumentation}
            onItemSelect={handleItemSelect}
          />

          {/* Main Content */}
          <div className="col-md-9">
            {/* Page-specific content based on currentPage */}
            {currentPage === 'query' && (
              <QueryPage
                sqlAgentStatus={sqlAgentStatus}
                query={query}
                setQuery={setQuery}
                executeQuery={executeQuery}
                isLoading={isLoading}
                handleKeyPress={handleKeyPress}
                entityRecognition={entityRecognition}
                businessContext={businessContext}
                sqlValidation={sqlValidation}
                generatedSql={generatedSql}
                copySqlToClipboard={copySqlToClipboard}
                queryExecution={queryExecution}
                optimizationSuggestions={optimizationSuggestions}
                results={results}
              />
            )}

            {/* Relationships Page */}
            {currentPage === 'relationships' && (
              <RelationshipsPage />
            )}

            {/* Schema Page */}
            {currentPage === 'schema' && (
              <SchemaPage />
            )}

            {/* Documentation Page */}
            {currentPage === 'documentation' && (
              <DocumentationPage />
            )}
          </div>
        </div>
      </div>

      {/* Item Details Modal - Rendered in main view */}
      <ItemDetailsModal
        showItemDetails={showItemDetails}
        setShowItemDetails={setShowItemDetails}
        selectedItem={selectedItem}
      />
    </div>
  );
}

export default App;