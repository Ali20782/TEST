# Test Suite Documentation

## Overview

This directory contains comprehensive tests for the Process Mining Platform, including unit tests, integration tests, and end-to-end tests.

## Test Structure

```
scripts/tests/
├── conftest.py                 # Shared fixtures and configuration
├── run_tests.py               # Master test runner
├── test_api_server.py         # API endpoint tests
├── test_data_processing.py    # Data processing tests
├── test_database.py           # Database operations tests
├── test_embedding_service.py  # Embedding service tests
└── test_integration.py        # End-to-end integration tests
```

## Running Tests

### Quick Start

```bash
# Run all tests
python scripts/tests/run_tests.py all

# Run unit tests only
python scripts/tests/run_tests.py unit

# Run integration tests only
python scripts/tests/run_tests.py integration

# Quick test (fail fast)
python scripts/tests/run_tests.py quick
```

### Using Pytest Directly

```bash
# Run all tests
pytest scripts/tests/ -v

# Run specific test file
pytest scripts/tests/test_api_server.py -v

# Run tests with specific marker
pytest scripts/tests/ -m unit -v

# Run with coverage
pytest scripts/tests/ --cov=scripts --cov-report=html
```

### Test Markers

Tests are marked for easy filtering:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.database` - Requires database
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.embedding` - Embedding model tests

Example:
```bash
# Run only unit tests
pytest -m unit

# Run everything except slow tests
pytest -m "not slow"

# Run database tests only
pytest -m database
```

## Test Suites

### 1. API Server Tests (`test_api_server.py`)

Tests FastAPI endpoints and middleware.

**Test Classes:**
- `TestHealthEndpoint` - Health check endpoint
- `TestStructuredIngestion` - CSV/XLSX file ingestion
- `TestUnstructuredIngestion` - Text/DOCX file ingestion
- `TestErrorHandling` - Error scenarios
- `TestConcurrency` - Concurrent request handling
- `TestResponseFormat` - Response consistency
- `TestFileValidation` - File validation logic

**Coverage:**
- ✅ Health endpoint
- ✅ File upload validation
- ✅ Data ingestion (structured & unstructured)
- ✅ Error handling
- ✅ Response formats
- ✅ Concurrency

### 2. Data Processing Tests (`test_data_processing.py`)

Tests file processing, validation, and transformation.

**Test Classes:**
- `TestCSVProcessing` - CSV file handling
- `TestXLSXProcessing` - Excel file handling
- `TestTextExtraction` - Text extraction from various formats
- `TestSchemaValidation` - Event log schema validation
- `TestDataTransformation` - Data transformation logic
- `TestEncodingDetection` - File encoding detection
- `TestMetricsCalculation` - Metrics computation
- `TestErrorHandling` - Error scenarios

**Coverage:**
- ✅ CSV/XLSX parsing
- ✅ Text extraction (TXT/DOCX/PDF)
- ✅ Schema validation
- ✅ Data transformation
- ✅ Encoding detection
- ✅ Error handling

### 3. Database Tests (`test_database.py`)

Tests database operations and PGVector functionality.

**Test Classes:**
- `TestDatabaseConnection` - Connection management
- `TestProjectOperations` - CRUD operations for projects
- `TestEventLogOperations` - Event log storage
- `TestEmbeddingOperations` - Vector storage
- `TestDocumentOperations` - Document metadata
- `TestVectorSearch` - Similarity search
- `TestTransactions` - Transaction handling
- `TestPerformance` - Performance benchmarks

**Coverage:**
- ✅ Database connectivity
- ✅ Project CRUD
- ✅ Event log insertion
- ✅ Vector embeddings
- ✅ Similarity search
- ✅ Transaction rollback
- ✅ Performance

### 4. Embedding Service Tests (`test_embedding_service.py`)

Tests text embedding generation and similarity computation.

**Test Classes:**
- `TestEmbeddingService` - Basic embedding
- `TestBatchEmbedding` - Batch processing
- `TestSimilarity` - Similarity computation
- `TestEmbeddingProperties` - Mathematical properties
- `TestPerformance` - Performance metrics
- `TestErrorHandling` - Error scenarios
- `TestModelConfiguration` - Model settings

**Coverage:**
- ✅ Single text embedding
- ✅ Batch embedding
- ✅ Similarity computation
- ✅ Vector normalization
- ✅ Performance benchmarks
- ✅ Error handling

### 5. Integration Tests (`test_integration.py`)

End-to-end workflow tests.

**Test Classes:**
- `TestAPIAvailability` - Service availability
- `TestProjectWorkflow` - Complete project lifecycle
- `TestStructuredDataWorkflow` - Data ingestion workflow
- `TestUnstructuredDataWorkflow` - Document processing
- `TestEndToEndWorkflow` - Full system test
- `TestErrorHandling` - Error scenarios
- `TestPerformance` - Load testing
- `TestDataIntegrity` - Data consistency

**Coverage:**
- ✅ End-to-end workflows
- ✅ Data consistency
- ✅ Error handling
- ✅ Concurrent operations
- ✅ Performance under load

## Test Coverage

Generate coverage report:

```bash
pytest scripts/tests/ --cov=scripts --cov-report=html
```

View report:
```bash
open htmlcov/index.html
```

Target coverage: **> 80%**

## CI/CD Integration

Tests are designed for CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    python scripts/tests/run_tests.py all
    
- name: Generate Coverage
  run: |
    pytest scripts/tests/ --cov=scripts --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

## Writing New Tests

### Test Template

```python
import pytest

class TestNewFeature:
    """Test new feature description"""
    
    @pytest.mark.unit
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        input_data = "test"
        
        # Act
        result = process(input_data)
        
        # Assert
        assert result is not None
    
    @pytest.mark.integration
    def test_integration(self, client):
        """Test integration with other components"""
        response = client.get("/endpoint")
        assert response.status_code == 200
```

### Best Practices

1. **Use descriptive names**: Test names should clearly describe what they test
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **One assertion per test**: Keep tests focused
4. **Use fixtures**: Reuse common setup code
5. **Mark appropriately**: Use pytest markers for categorization
6. **Document tests**: Add docstrings to test classes and methods
7. **Clean up**: Use fixtures for setup and teardown

### Fixtures

Common fixtures are defined in `conftest.py`:

```python
@pytest.fixture
def sample_csv():
    """Fixture that creates sample CSV"""
    # Setup
    yield data
    # Teardown
```

## Troubleshooting

### Tests Failing

1. **Check server is running**: `curl http://localhost:8000/health`
2. **Check database**: `docker-compose ps`
3. **View logs**: `docker-compose logs -f`
4. **Check dependencies**: `pip list`

### Slow Tests

Use markers to skip slow tests:
```bash
pytest -m "not slow"
```

### Database Tests Failing

Reset database:
```bash
docker-compose down -v
docker-compose up -d
```

### Import Errors

Ensure you're in project root:
```bash
cd /path/to/project
python -m pytest scripts/tests/
```

## Performance Benchmarks

Expected test durations:

- **Unit Tests**: < 30 seconds
- **Integration Tests**: < 2 minutes
- **Full Suite**: < 3 minutes

Slow tests are marked with `@pytest.mark.slow`

## Continuous Improvement

- Add tests for new features
- Maintain > 80% coverage
- Review and update fixtures
- Keep tests fast and focused
- Document edge cases
