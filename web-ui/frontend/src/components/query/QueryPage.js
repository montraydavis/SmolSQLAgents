import React from 'react';
import SQLAgentStatus from './SQLAgentStatus';
import QueryInput from './QueryInput';
import EntityRecognitionResults from './EntityRecognitionResults';
import BusinessContext from './BusinessContext';
import SQLGeneration from './SQLGeneration';
import QueryResults from './QueryResults';
import OptimizationSuggestions from './OptimizationSuggestions';

const QueryPage = ({
  sqlAgentStatus,
  query,
  setQuery,
  executeQuery,
  isLoading,
  handleKeyPress,
  entityRecognition,
  businessContext,
  sqlValidation,
  generatedSql,
  copySqlToClipboard,
  queryExecution,
  optimizationSuggestions,
  results
}) => {
  console.log('QueryPage - results prop:', results);
  console.log('QueryPage - queryExecution prop:', queryExecution);
  return (
    <>
      {/* SQL Agent Status */}
      <SQLAgentStatus sqlAgentStatus={sqlAgentStatus} />

      {/* Query Input */}
      <QueryInput
        query={query}
        setQuery={setQuery}
        executeQuery={executeQuery}
        isLoading={isLoading}
        handleKeyPress={handleKeyPress}
      />

      {/* Entity Recognition Results */}
      <EntityRecognitionResults entityRecognition={entityRecognition} />

      {/* Business Context */}
      <BusinessContext businessContext={businessContext} />

      {/* SQL Generation */}
      <SQLGeneration
        sqlValidation={sqlValidation}
        generatedSql={generatedSql}
        copySqlToClipboard={copySqlToClipboard}
      />

      {/* Query Results */}
      <QueryResults queryExecution={queryExecution} results={results} />

      {/* Optimization Suggestions */}
      <OptimizationSuggestions optimizationSuggestions={optimizationSuggestions} />
    </>
  );
};

export default QueryPage; 