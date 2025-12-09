#!/bin/bash

# Test Runner Script for Process Mining Platform
# Runs all tests with proper configuration

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  Process Mining Platform Test Suite${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if server is running
echo -e "${BLUE}Checking if API server is running...${NC}"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API server is running${NC}\n"
else
    echo -e "${RED}❌ API server is not running${NC}"
    echo -e "${YELLOW}Please start the server first:${NC}"
    echo -e "  ./manage.sh start"
    echo -e ""
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not found${NC}"
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip install pytest pytest-cov
fi

# Parse command line arguments
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    unit)
        echo -e "${BLUE}Running unit tests only...${NC}\n"
        pytest tests/test_database.py tests/test_file_processors.py tests/test_embedding_service.py -v
        ;;
    integration)
        echo -e "${BLUE}Running integration tests only...${NC}\n"
        pytest tests/test_integration.py -v
        ;;
    api)
        echo -e "${BLUE}Running API tests only...${NC}\n"
        python -m scripts.test_api
        ;;
    database)
        echo -e "${BLUE}Running database tests only...${NC}\n"
        pytest tests/test_database.py -v
        ;;
    quick)
        echo -e "${BLUE}Running quick test suite...${NC}\n"
        pytest tests/ -v --tb=line -x
        ;;
    coverage)
        echo -e "${BLUE}Running tests with coverage...${NC}\n"
        pytest tests/ -v --cov=scripts --cov-report=html --cov-report=term
        echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    all)
        echo -e "${BLUE}Running all tests...${NC}\n"
        
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}Unit Tests${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        pytest tests/test_database.py tests/test_file_processors.py tests/test_embedding_service.py -v
        
        echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}Integration Tests${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        pytest tests/test_integration.py -v
        
        echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}API Endpoint Tests${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        python -m scripts.test_api
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo -e "\n${YELLOW}Usage:${NC}"
        echo -e "  ./run_tests.sh [type]"
        echo -e ""
        echo -e "${YELLOW}Available types:${NC}"
        echo -e "  ${GREEN}all${NC}         - Run all tests (default)"
        echo -e "  ${GREEN}unit${NC}        - Run unit tests only"
        echo -e "  ${GREEN}integration${NC} - Run integration tests only"
        echo -e "  ${GREEN}api${NC}         - Run API endpoint tests only"
        echo -e "  ${GREEN}database${NC}    - Run database tests only"
        echo -e "  ${GREEN}quick${NC}       - Run quick test suite (fail fast)"
        echo -e "  ${GREEN}coverage${NC}    - Run tests with coverage report"
        echo -e ""
        exit 1
        ;;
esac

# Test results
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✅ All tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}\n"
else
    echo -e "\n${RED}========================================${NC}"
    echo -e "${RED}  ❌ Some tests failed${NC}"
    echo -e "${RED}========================================${NC}\n"
    exit 1
fi