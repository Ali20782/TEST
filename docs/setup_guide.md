# Quick Setup & Testing Guide

## Prerequisites

- Docker & Docker Compose installed
- Python 3.10 or higher
- Git

## Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/AliDev110/AI-Powered-Conversational-Process-Int-Platform
cd AI-Powered-Conversational-Process-Int-Platform
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and set your credentials:

```bash
# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_NAME=process_db
DB_USER=user
DB_PASSWORD=your_secure_password

# AI Configuration (optional for initial testing)
GEMINI_API_KEY=your_api_key_here
```

### 3. Start Docker Containers

```bash
docker-compose up -d
```

Wait for services to start (~30 seconds):

```bash
docker-compose ps
```

You should see both `db` and `backend` services running.

### 4. Verify Services

Check API health:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "api_status": "ok",
  "database_status": "ok"
}
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
python scripts/tests/run_tests.py all
```

### Run Specific Test Suites

**Unit Tests Only:**
```bash
python scripts/tests/run_tests.py unit
```

**Integration Tests Only:**
```bash
python scripts/tests/run_tests.py integration
```

**Quick Tests (Fail Fast):**
```bash
python scripts/tests/run_tests.py quick
```

### Run Individual Test Files

**API Server Tests:**
```bash
pytest scripts/tests/test_api_server.py -v
```

**Database Tests:**
```bash
pytest scripts/tests/test_database.py -v
```

**Data Processing Tests:**
```bash
pytest scripts/tests/test_data_processing.py -v
```

**Embedding Service Tests:**
```bash
pytest scripts/tests/test_embedding_service.py -v
```

**Integration Tests:**
```bash
pytest scripts/tests/test_integration.py -v
```

### Test Coverage Report

```bash
pytest scripts/tests/ --cov=scripts --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Troubleshooting

### Services Not Starting

Check logs:
```bash
docker-compose logs -f
```

Restart services:
```bash
docker-compose down
docker-compose up -d
```

### Database Connection Issues

Ensure database is ready:
```bash
docker-compose exec db pg_isready -U user -d process_db
```

Reset database:
```bash
docker-compose down -v
docker-compose up -d
```

### Test Failures

Check if API server is running:
```bash
curl http://localhost:8000/health
```

Check test logs:
```bash
cat test_results.json
```

## Stopping Services

```bash
docker-compose down
```

To remove all data:
```bash
docker-compose down -v
```

## API Documentation

Once running, access interactive API docs:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Common Commands

**View logs:**
```bash
docker-compose logs -f backend
docker-compose logs -f db
```

**Access database:**
```bash
docker-compose exec db psql -U user -d process_db
```

**Rebuild containers:**
```bash
docker-compose up -d --build
```

**Check container status:**
```bash
docker-compose ps
```

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review test output: `cat test_results.json`
3. Ensure all prerequisites are installed
4. Verify `.env` file is configured correctly
