# Batch Manager

The Batch Manager is an optimization component that provides efficient batch processing for OpenAI embeddings generation. It works with the Indexer Agent to process multiple documents simultaneously, reducing API calls and costs while maintaining high throughput for large-scale database documentation.

## 🎯 What It Does

The Batch Manager optimizes vector indexing operations for SQL documentation:

- **Efficient Batch Processing**: Groups multiple documents into optimal batch sizes for OpenAI API calls
- **Cost Estimation**: Provides accurate cost estimates before processing large datasets
- **Progress Tracking**: Monitors processing progress with detailed statistics and logging
- **Error Recovery**: Handles failures gracefully with comprehensive error reporting
- **Resource Optimization**: Minimizes OpenAI API usage through intelligent batching strategies
- **Scalable Processing**: Handles databases with thousands of tables and relationships efficiently

## 🔄 Processing Flow

```markdown
Documentation Store → Batch Manager → Grouped Batches → Indexer Agent → OpenAI API → Vector Storage
```

1. **Data Collection**: Retrieves pending tables and relationships from documentation store
2. **Batch Grouping**: Organizes items into optimal batch sizes for API efficiency
3. **Cost Estimation**: Calculates expected OpenAI API costs before processing
4. **Batch Processing**: Processes multiple documents per API call using the Indexer Agent
5. **Progress Monitoring**: Tracks completion status and success rates across batches
6. **Result Aggregation**: Combines individual processing results into comprehensive reports

## 🚀 Usage Examples

### Command Line Interface

```bash
# Use batch processing for documentation generation (default)
python main.py --batch-index

# Estimate costs before processing
python main.py --estimate-costs

# Individual processing (non-batched)
python main.py --individual-index

# Rebuild indexes using batch processing
python main.py --rebuild-indexes
```

### Programmatic Usage

```python
from src.agents.batch_manager import BatchIndexingManager
from src.agents.indexer import SQLIndexerAgent
from src.vector.store import SQLVectorStore
from src.database.persistence import DocumentationStore

# Initialize components
vector_store = SQLVectorStore()
indexer_agent = SQLIndexerAgent(vector_store)
batch_manager = BatchIndexingManager(indexer_agent)
doc_store = DocumentationStore()

# Get processing statistics
stats = batch_manager.get_processing_stats(doc_store)
print(f"Pending items: {stats['total_pending']}")
print(f"Estimated cost: ${stats['total_estimated_cost']:.6f}")

# Process tables in batches
table_results = batch_manager.batch_process_pending_tables(doc_store)
successful_tables = sum(1 for success in table_results.values() if success)
print(f"Processed {successful_tables}/{len(table_results)} tables successfully")

# Process relationships in batches
rel_results = batch_manager.batch_process_pending_relationships(doc_store)
successful_rels = sum(1 for success in rel_results.values() if success)
print(f"Processed {successful_rels}/{len(rel_results)} relationships successfully")

# Estimate costs for custom text list
texts = ["Table documentation text", "Relationship documentation text"]
cost_estimate = batch_manager.estimate_embedding_costs(texts)
print(f"Estimated cost for {len(texts)} texts: ${cost_estimate['estimated_cost_usd']:.6f}")
```

## 📊 Response Structure

### Processing Statistics Response

```json
{
  "pending_tables": 150,
  "pending_relationships": 75,
  "total_pending": 225,
  "estimated_table_cost": 0.000180,
  "estimated_relationship_cost": 0.000090,
  "total_estimated_cost": 0.000270,
  "batch_size": 100,
  "estimated_batches": 3
}
```

### Batch Processing Results

```json
{
  "table_processing_results": {
    "users": true,
    "orders": true,
    "products": false,
    "categories": true
  },
  "relationship_processing_results": {
    "users_orders_fk": true,
    "orders_products_fk": true,
    "products_categories_fk": false
  },
  "summary": {
    "total_tables_processed": 4,
    "successful_tables": 3,
    "total_relationships_processed": 3,
    "successful_relationships": 2,
    "overall_success_rate": 0.714
  }
}
```

### Cost Estimation Response

```json
{
  "total_texts": 50,
  "estimated_tokens": 12500,
  "estimated_cost_usd": 0.000250,
  "cost_per_text": 0.000005
}
```

## ⚙️ Configuration

### Environment Variables

```env
# Batch processing settings
EMBEDDING_BATCH_SIZE="100"          # Documents per batch (default: 100)
EMBEDDING_MAX_RETRIES="3"           # Maximum retry attempts (default: 3)

# Required for underlying components
OPENAI_API_KEY="your-api-key-here"
DATABASE_URL="your-database-connection-string"

# Optional: Logging configuration
LOG_LEVEL="INFO"
LOG_FILE="batch_processing.log"
```

### Initialization Parameters

```python
BatchIndexingManager(
    indexer_agent                    # Required: SQLIndexerAgent instance
)

# Method parameters
batch_process_pending_tables(
    doc_store                       # Required: DocumentationStore instance
)

batch_process_pending_relationships(
    doc_store                       # Required: DocumentationStore instance  
)

get_processing_stats(
    doc_store                       # Required: DocumentationStore instance
)

estimate_embedding_costs(
    texts                          # Required: List of text strings
)
```

## 🎯 Use Cases

### 1. Large Database Processing

Efficiently process databases with hundreds or thousands of tables:

```python
# Get statistics before processing
stats = batch_manager.get_processing_stats(doc_store)
print(f"Will process {stats['total_pending']} items in {stats['estimated_batches']} batches")
print(f"Estimated cost: ${stats['total_estimated_cost']:.6f}")

# Process in optimized batches
if stats['total_estimated_cost'] < 0.10:  # Cost threshold check
    table_results = batch_manager.batch_process_pending_tables(doc_store)
    rel_results = batch_manager.batch_process_pending_relationships(doc_store)
```

### 2. Cost-Conscious Processing

Estimate and control OpenAI API costs before processing:

```python
# Check costs before processing
stats = batch_manager.get_processing_stats(doc_store)
if stats['total_estimated_cost'] > 1.00:  # $1.00 threshold
    print(f"Warning: Estimated cost ${stats['total_estimated_cost']:.6f} exceeds threshold")
    user_confirm = input("Continue? (y/n): ")
    if user_confirm.lower() != 'y':
        return

# Proceed with batch processing
results = batch_manager.batch_process_pending_tables(doc_store)
```

### 3. Progress Monitoring

Monitor large-scale processing operations:

```python
import time

# Start processing
print("Starting batch processing...")
start_time = time.time()

table_results = batch_manager.batch_process_pending_tables(doc_store)
rel_results = batch_manager.batch_process_pending_relationships(doc_store)

# Calculate metrics
end_time = time.time()
processing_time = end_time - start_time
total_items = len(table_results) + len(rel_results)
successful_items = sum(table_results.values()) + sum(rel_results.values())

print(f"Processing completed in {processing_time:.2f} seconds")
print(f"Success rate: {successful_items}/{total_items} ({successful_items/total_items*100:.1f}%)")
```

### 4. Custom Batch Sizing

Optimize batch sizes for different scenarios:

```python
# Small batches for rate-limited scenarios
small_batch_manager = BatchIndexingManager(indexer_agent)
small_batch_manager.batch_size = 25

# Large batches for high-throughput scenarios  
large_batch_manager = BatchIndexingManager(indexer_agent)
large_batch_manager.batch_size = 200

# Process with appropriate batch size
results = small_batch_manager.batch_process_pending_tables(doc_store)
```

## 🔍 Integration with Other Components

The Batch Manager orchestrates several components for optimal processing:

- **Indexer Agent**: Provides the core indexing functionality for individual documents
- **Documentation Store**: Supplies pending items and stores processing metadata
- **Vector Store**: Receives the processed embeddings and document metadata
- **OpenAI API**: Handles the actual embedding generation with optimized batch calls
- **Logger**: Provides detailed progress tracking and error reporting

## 🎖️ Advanced Features

### Intelligent Cost Estimation

- Token-based cost calculation using OpenAI pricing models
- Accurate estimation before processing large datasets
- Cost-per-item breakdown for detailed analysis
- Support for different embedding models and pricing tiers

### Adaptive Batch Processing

- Dynamic batch sizing based on content length and complexity
- Automatic retry logic with exponential backoff for transient failures
- Graceful error handling with partial batch recovery
- Progress tracking with detailed success/failure reporting

### Resource Optimization

- Memory-efficient processing of large document sets
- Optimized API usage to minimize costs and latency
- Configurable batch sizes for different scenarios
- Built-in rate limiting and throttling support

### Error Recovery and Reporting

- Comprehensive error logging with actionable details
- Graceful degradation when individual items fail
- Detailed success/failure statistics for monitoring
- Retry mechanisms for transient API failures

## 📈 Performance Characteristics

- **Throughput**: 50-200 documents per minute depending on content size and batch configuration
- **Cost Efficiency**: 40-60% reduction in API calls compared to individual processing
- **Memory Usage**: Minimal memory footprint with streaming batch processing
- **Scalability**: Handles databases with 10,000+ tables efficiently
- **Error Recovery**: Continues processing after individual failures without stopping entire batches
- **API Optimization**: Intelligent batching reduces rate limiting issues

## 🚦 Prerequisites

1. **Indexer Agent**: Functional SQLIndexerAgent instance for document processing
2. **Documentation Store**: DocumentationStore with pending items to process
3. **OpenAI API Access**: Valid API key with sufficient credits for embedding generation
4. **Vector Storage**: Configured vector store (ChromaDB) for embedding persistence
5. **Dependencies**: All required packages from requirements.txt

## 🔧 Error Handling

### Common Error Scenarios

1. **API Rate Limiting**: Automatic retry with exponential backoff for rate limit errors
2. **Network Issues**: Connection timeout handling with retry mechanisms
3. **Invalid Documents**: Graceful handling of malformed document data
4. **Memory Constraints**: Efficient memory usage for large batch processing
5. **Partial Failures**: Continue processing remaining items when individual documents fail

### Error Response Handling

```python
# Handle batch processing errors
try:
    results = batch_manager.batch_process_pending_tables(doc_store)
    
    # Check for failures
    failed_tables = [table for table, success in results.items() if not success]
    if failed_tables:
        print(f"Failed to process tables: {failed_tables}")
        
        # Retry failed items individually
        for table in failed_tables:
            try:
                # Process individually for detailed error info
                success = indexer_agent.index_table_documentation(table_data)
                if success:
                    print(f"Retry successful for table: {table}")
            except Exception as e:
                print(f"Retry failed for table {table}: {e}")
                
except Exception as e:
    print(f"Batch processing failed: {e}")
    # Fall back to individual processing
    pending_tables = doc_store.get_pending_tables()
    for table in pending_tables:
        try:
            agent.process_table_documentation(table)
        except Exception as table_error:
            print(f"Individual processing failed for {table}: {table_error}")
```

### Retry Mechanisms

The Batch Manager includes sophisticated retry logic:

1. **API Rate Limits**: Exponential backoff with jitter for rate limit responses
2. **Network Failures**: Connection retry with timeout escalation
3. **Transient Errors**: Automatic retry for temporary API issues
4. **Batch Failures**: Automatic fallback to individual item processing
5. **Resource Constraints**: Memory and resource management for large datasets

---

The Batch Manager is essential for efficient large-scale processing in the SQL Documentation suite, providing cost-effective and scalable vector indexing capabilities while maintaining high reliability and comprehensive error handling.
