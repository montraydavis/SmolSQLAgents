# Business Agent

The Business Agent (BusinessContextAgent) is an intelligent component that gathers business context and domain knowledge for SQL generation. It uses concept matching, business rules, and domain expertise to provide rich business context that enhances the accuracy and relevance of generated SQL queries.

## 🎯 What It Does

The Business Agent provides sophisticated business context gathering:

- **Concept Matching**: Matches user queries to business concepts and domain knowledge
- **Business Rules**: Applies business rules and constraints to SQL generation
- **Domain Expertise**: Leverages domain-specific knowledge for better query understanding
- **Join Validation**: Validates that required table joins can be satisfied
- **Example Retrieval**: Finds relevant examples and patterns for similar queries
- **Entity Coverage**: Analyzes how well business concepts cover identified entities

## 🔄 Processing Flow

```markdown
User Query → Entity Analysis → Concept Loading → Concept Matching → Business Rules → Join Validation → Context Assembly
```

1. **Entity Analysis**: Analyzes identified database entities for business relevance
2. **Concept Loading**: Loads business concepts and domain knowledge for entities
3. **Concept Matching**: Matches user query to relevant business concepts
4. **Business Rules**: Applies business rules and constraints
5. **Join Validation**: Validates that required table relationships can be satisfied
6. **Context Assembly**: Combines all business context into comprehensive response

## 🚀 Usage Examples

### Command Line Interface

```bash
# Gather business context for customer analytics
python main.py --business-context "customer analytics" --entities "customers,orders"

# Business context with custom concepts directory
python main.py --business-context "user behavior" --concepts-dir "custom/concepts"

# Business context for specific business domain
python main.py --business-context "sales performance" --domain "retail"
```

### Programmatic Usage

```python
from src.agents.business import BusinessContextAgent
from src.agents.factory import agent_factory

# Get business agent from factory
business_agent = agent_factory.get_business_agent()

# Gather business context
applicable_entities = ["customers", "orders", "products"]
business_context = business_agent.gather_business_context(
    user_query="customer retention analysis",
    applicable_entities=applicable_entities
)

# Check business context results
if business_context["success"]:
    print(f"Matched concepts: {business_context['matched_concepts']}")
    print(f"Business instructions: {business_context['business_instructions']}")
    print(f"Entity coverage: {business_context['entity_coverage']}")
else:
    print(f"Business context failed: {business_context['error']}")
```

## 📊 Response Structure

### Successful Business Context Response

```json
{
  "success": true,
  "matched_concepts": [
    {
      "name": "customer_retention",
      "description": "Customer retention and loyalty analysis",
      "target_entities": ["customers", "orders"],
      "required_joins": ["customers.customer_id = orders.customer_id"],
      "similarity": 0.85
    },
    {
      "name": "customer_analytics",
      "description": "Customer behavior and analytics",
      "target_entities": ["customers", "orders", "products"],
      "required_joins": ["customers.customer_id = orders.customer_id", "orders.product_id = products.product_id"],
      "similarity": 0.72
    }
  ],
  "business_instructions": [
    {
      "concept": "customer_retention",
      "instructions": "Use customer_id for joins, filter by date ranges, calculate retention rates",
      "similarity": 0.85
    },
    {
      "concept": "customer_analytics",
      "instructions": "Include customer demographics, order patterns, and product preferences",
      "similarity": 0.72
    }
  ],
  "relevant_examples": [
    {
      "example": "SELECT customer_id, COUNT(DISTINCT order_date) as order_frequency FROM orders GROUP BY customer_id",
      "similarity": 0.78,
      "concept_name": "customer_retention"
    }
  ],
  "join_validation": {
    "customer_retention": {
      "valid": true,
      "satisfied_joins": ["customers.customer_id = orders.customer_id"],
      "unsatisfied_joins": []
    },
    "customer_analytics": {
      "valid": true,
      "satisfied_joins": ["customers.customer_id = orders.customer_id", "orders.product_id = products.product_id"],
      "unsatisfied_joins": []
    }
  },
  "entity_coverage": {
    "total_entities": 3,
    "entities_with_concepts": 3
  }
}
```

### Empty Business Context Response

```json
{
  "success": true,
  "matched_concepts": [],
  "business_instructions": [],
  "relevant_examples": [],
  "join_validation": {},
  "entity_coverage": {
    "total_entities": 0,
    "entities_with_concepts": 0
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Failed to load business concepts",
  "matched_concepts": [],
  "business_instructions": [],
  "relevant_examples": [],
  "join_validation": {},
  "entity_coverage": {
    "total_entities": 0,
    "entities_with_concepts": 0
  }
}
```

## 🧠 Processing Algorithm

The Business Agent implements sophisticated concept matching and business rule application:

### Stage 1: Concept Loading
```python
def gather_business_context(self, user_query: str, applicable_entities: List[str]):
    # Load concepts for identified entities
    concepts = self.concept_loader.get_concepts_for_entities(applicable_entities)
    
    # Match concepts to user query
    matched_concepts = self.concept_matcher.match_concepts_to_query(user_query, concepts)
    
    # Extract business instructions and examples
    business_instructions = self._extract_business_instructions(matched_concepts)
    relevant_examples = self._get_relevant_examples(matched_concepts, user_query)
    
    # Validate joins
    join_validation = self._validate_required_joins(applicable_entities, matched_concepts)
    
    return self._format_business_context(matched_concepts, business_instructions, 
                                       relevant_examples, join_validation)
```

### Stage 2: Concept Matching
```python
def match_concepts_to_query(self, user_query: str, concepts: List[BusinessConcept]):
    # Use semantic similarity to match concepts
    matches = []
    for concept in concepts:
        similarity = self._calculate_concept_similarity(user_query, concept)
        if similarity > 0.5:  # Threshold for relevance
            matches.append((concept, similarity))
    
    # Sort by similarity score
    return sorted(matches, key=lambda x: x[1], reverse=True)
```

### Stage 3: Join Validation
```python
def _validate_required_joins(self, entities: List[str], matched_concepts: List[Tuple]):
    validation_results = {}
    
    for concept, similarity in matched_concepts:
        required_entities = self._extract_entities_from_joins(concept.required_joins)
        available_entities = set(entities)
        missing_entities = required_entities - available_entities
        
        validation_results[concept.name] = {
            "valid": len(missing_entities) == 0,
            "missing_entities": list(missing_entities),
            "satisfied_joins": [join for join in concept.required_joins 
                              if self._can_satisfy_join(join, available_entities)],
            "unsatisfied_joins": [join for join in concept.required_joins 
                                 if not self._can_satisfy_join(join, available_entities)]
        }
    
    return validation_results
```

## ⚙️ Configuration

### Environment Variables

```env
# Required for business context
OPENAI_API_KEY="your-api-key-here"

# Optional: Business concepts directory
CONCEPTS_DIRECTORY="src/agents/concepts"

# Optional: Concept matching settings
CONCEPT_SIMILARITY_THRESHOLD="0.5"
MAX_CONCEPTS_PER_QUERY="5"

# Optional: Logging configuration
LOG_LEVEL="INFO"
LOG_FILE="business_agent.log"
```

### Initialization Parameters

```python
BusinessContextAgent(
    indexer_agent=None,              # Optional: SQLIndexerAgent for semantic search
    concepts_dir="src/agents/concepts",  # Optional: Concepts directory path
    shared_llm_model=None,          # Optional: Shared LLM model
    shared_concept_loader=None,      # Optional: Shared concept loader
    shared_concept_matcher=None,     # Optional: Shared concept matcher
    database_tools=None              # Optional: Database tools
)

# Method parameters
gather_business_context(
    user_query,                      # Required: Natural language query
    applicable_entities              # Required: List of entity names
)
```

## 🎯 Use Cases

### 1. Customer Analytics Context

Gather business context for customer analysis:

```python
# Customer analytics query
business_context = business_agent.gather_business_context(
    user_query="customer behavior analysis",
    applicable_entities=["customers", "orders", "products"]
)

# Check matched concepts
for concept in business_context["matched_concepts"]:
    print(f"Concept: {concept['name']}")
    print(f"Description: {concept['description']}")
    print(f"Similarity: {concept['similarity']}")
    print(f"Required joins: {concept['required_joins']}")
```

### 2. Sales Performance Analysis

Business context for sales analysis:

```python
# Sales performance query
business_context = business_agent.gather_business_context(
    user_query="sales performance by region",
    applicable_entities=["sales", "regions", "products", "customers"]
)

# Apply business instructions
for instruction in business_context["business_instructions"]:
    print(f"Business rule: {instruction['instructions']}")
    print(f"Concept: {instruction['concept']}")
    print(f"Confidence: {instruction['similarity']}")
```

### 3. Join Validation

Validate that required joins can be satisfied:

```python
# Check join validation
join_validation = business_context["join_validation"]

for concept_name, validation in join_validation.items():
    if validation["valid"]:
        print(f"✅ {concept_name}: All joins satisfied")
    else:
        print(f"❌ {concept_name}: Missing entities {validation['missing_entities']}")
        print(f"   Unsatisfied joins: {validation['unsatisfied_joins']}")
```

### 4. Entity Coverage Analysis

Analyze how well business concepts cover entities:

```python
# Check entity coverage
coverage = business_context["entity_coverage"]
print(f"Total entities: {coverage['total_entities']}")
print(f"Entities with concepts: {coverage['entities_with_concepts']}")
print(f"Coverage percentage: {coverage['entities_with_concepts']/coverage['total_entities']*100:.1f}%")
```

## 🔍 Integration with Other Agents

The Business Agent works seamlessly with other components:

- **Entity Recognition Agent**: Receives identified entities for context analysis
- **Concept Loader**: Loads business concepts and domain knowledge
- **Concept Matcher**: Matches queries to relevant business concepts
- **NL2SQL Agent**: Provides business context for SQL generation
- **Integration Agent**: Contributes business context to complete pipeline

## 🎖️ Advanced Features

### Intelligent Concept Matching

- Semantic similarity using OpenAI embeddings
- Multi-factor concept relevance scoring
- Configurable similarity thresholds
- Support for complex business domains

### Business Rule Application

- Domain-specific business rules and constraints
- Join requirement validation
- Entity relationship analysis
- Business logic enforcement

### Example Retrieval

- Similar example identification
- Pattern matching for query optimization
- Historical query analysis
- Best practice recommendations

### Join Validation

- Automatic join requirement analysis
- Entity availability checking
- Join satisfaction validation
- Missing entity identification

## 📈 Performance Characteristics

- **Concept Loading**: 0.1-0.5 seconds for concept retrieval
- **Concept Matching**: 1-3 seconds for semantic matching
- **Join Validation**: Sub-second for join analysis
- **Memory Usage**: Efficient concept caching and reuse
- **Scalability**: Handles complex business domains with hundreds of concepts
- **Accuracy**: High precision concept matching with configurable thresholds

## 🚦 Prerequisites

1. **Business Concepts**: YAML-based business concept definitions
2. **OpenAI API Access**: Valid API key for semantic matching
3. **Entity Recognition**: Functional entity recognition for input
4. **Concept Components**: Concept loader and matcher components
5. **Dependencies**: All required packages from requirements.txt

## 🔧 Error Handling

### Common Error Scenarios

1. **Concept Loading Failures**: Missing concept files, invalid YAML
2. **Matching Errors**: API failures, invalid similarity calculations
3. **Join Validation Errors**: Invalid join syntax, missing entities
4. **Entity Coverage Issues**: No concepts found for entities

### Error Response Handling

```python
# Handle business context errors
try:
    business_context = business_agent.gather_business_context(
        user_query="customer analysis",
        applicable_entities=["customers", "orders"]
    )
    
    if not business_context["success"]:
        error = business_context.get("error", "Unknown error")
        
        if "Failed to load concepts" in error:
            print("Business concepts not found")
            # Use default business context
        elif "Concept matching failed" in error:
            print("Unable to match business concepts")
            # Continue with minimal context
        elif "Join validation failed" in error:
            print("Join requirements cannot be satisfied")
            # Provide alternative suggestions
            
except Exception as e:
    print(f"Business context gathering failed: {e}")
    # Implement fallback mechanisms
```

### Recovery Mechanisms

1. **Concept Fallback**: Use default concepts when loading fails
2. **Matching Fallback**: Use keyword matching when semantic matching fails
3. **Join Fallback**: Provide simplified joins when complex joins fail
4. **Entity Fallback**: Use entity name matching when concept matching fails

---

The Business Agent provides sophisticated business context gathering with intelligent concept matching, business rule application, and comprehensive join validation, ensuring that generated SQL queries incorporate relevant domain knowledge and business constraints for accurate and meaningful results. 