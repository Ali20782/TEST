#!/bin/bash

# Validation Script for Milestone 2 Setup
# Checks all prerequisites and configurations

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ERRORS=$((ERRORS + 1))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

check_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# 1. CHECK FILE STRUCTURE
# ============================================================================

print_header "Checking File Structure"

required_files=(
    "docker-compose.yml"
    "Dockerfile"
    ".env.example"
    "requirements.txt"
    "requirements-backend.txt"
    "requirements-testing.txt"
    "manage.sh"
    "run_tests.sh"
    "pytest.ini"
    "scripts/api_server.py"
    "scripts/database.py"
    "scripts/file_processors.py"
    "scripts/embedding_service.py"
    "scripts/test_api.py"
    "scripts/init_db.sql"
    "tests/__init__.py"
    "tests/test_database.py"
    "tests/test_file_processors.py"
    "tests/test_embedding_service.py"
    "tests/test_integration.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "Found: $file"
    else
        check_fail "Missing: $file"
    fi
done

# Check directories
required_dirs=(
    "scripts"
    "tests"
    "data/clean"
    "data/synthetic"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "Found directory: $dir"
    else
        check_warn "Missing directory: $dir (will be created)"
        mkdir -p "$dir"
    fi
done

# ============================================================================
# 2. CHECK DOCKER
# ============================================================================

print_header "Checking Docker"

if command -v docker &> /dev/null; then
    check_pass "Docker is installed"
    docker --version
else
    check_fail "Docker is not installed"
fi

if command -v docker-compose &> /dev/null; then
    check_pass "Docker Compose is installed"
    docker-compose --version
else
    check_fail "Docker Compose is not installed"
fi

# Check if Docker daemon is running
if docker info &> /dev/null; then
    check_pass "Docker daemon is running"
else
    check_fail "Docker daemon is not running"
fi

# ============================================================================
# 3. CHECK PYTHON
# ============================================================================

print_header "Checking Python"

if command -v python &> /dev/null; then
    check_pass "Python is installed"
    python --version
    
    # Check version
    version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$version >= 3.10" | bc -l) )); then
        check_pass "Python version >= 3.10"
    else
        check_fail "Python version < 3.10 (found $version)"
    fi
else
    check_fail "Python is not installed"
fi

# Check pip
if command -v pip &> /dev/null; then
    check_pass "pip is installed"
else
    check_fail "pip is not installed"
fi

# ============================================================================
# 4. CHECK ENVIRONMENT CONFIGURATION
# ============================================================================

print_header "Checking Environment Configuration"

if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    # Check for default passwords
    if grep -q "secure_password_change_me" .env; then
        check_warn "Using default password in .env - CHANGE IN PRODUCTION"
    else
        check_pass "Custom password configured"
    fi
    
    # Check required variables
    required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "DATABASE_URL")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            check_pass "Environment variable set: $var"
        else
            check_fail "Missing environment variable: $var"
        fi
    done
else
    check_warn ".env file not found - will use .env.example"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        check_info "Created .env from .env.example"
    fi
fi

# ============================================================================
# 5. CHECK PYTHON DEPENDENCIES
# ============================================================================

print_header "Checking Python Dependencies"

# Check virtual environment
if [ -d ".venv" ]; then
    check_pass "Virtual environment exists"
else
    check_warn "Virtual environment not found - run: python -m venv .venv"
fi

# Check if dependencies are installed
check_deps() {
    local dep=$1
    if python -c "import $dep" 2>/dev/null; then
        check_pass "Installed: $dep"
        return 0
    else
        check_fail "Missing: $dep"
        return 1
    fi
}

critical_deps=(
    "fastapi"
    "uvicorn"
    "pandas"
    "pm4py"
    "psycopg2"
    "sentence_transformers"
)

echo "Checking critical dependencies..."
for dep in "${critical_deps[@]}"; do
    check_deps "$dep" || true
done

# ============================================================================
# 6. CHECK SCRIPTS PERMISSIONS
# ============================================================================

print_header "Checking Script Permissions"

scripts=("manage.sh" "run_tests.sh" "validate_setup.sh")

for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            check_pass "$script is executable"
        else
            check_warn "$script is not executable - fixing..."
            chmod +x "$script"
            check_pass "Made $script executable"
        fi
    fi
done

# ============================================================================
# 7. CHECK DOCKER SERVICES
# ============================================================================

print_header "Checking Docker Services"

if docker-compose ps &> /dev/null; then
    # Check if services are running
    if docker-compose ps | grep -q "process_mining_db.*Up"; then
        check_pass "PostgreSQL container is running"
    else
        check_warn "PostgreSQL container is not running"
    fi
    
    if docker-compose ps | grep -q "process_mining_api.*Up"; then
        check_pass "API container is running"
    else
        check_warn "API container is not running"
    fi
else
    check_info "Docker services not started yet (run: ./manage.sh start)"
fi

# ============================================================================
# 8. CHECK API AVAILABILITY
# ============================================================================

print_header "Checking API Availability"

if curl -f http://localhost:8000/health &> /dev/null; then
    check_pass "API is accessible at http://localhost:8000"
    
    # Check health status
    health=$(curl -s http://localhost:8000/health | python -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    if [ "$health" = "healthy" ]; then
        check_pass "API health status: healthy"
    else
        check_warn "API health status: $health"
    fi
else
    check_info "API is not accessible (start with: ./manage.sh start)"
fi

# ============================================================================
# 9. CHECK DATABASE CONNECTIVITY
# ============================================================================

print_header "Checking Database Connectivity"

if docker ps | grep -q process_mining_db; then
    if docker exec process_mining_db pg_isready -U process_admin &> /dev/null; then
        check_pass "Database is accepting connections"
        
        # Check if database exists
        if docker exec process_mining_db psql -U process_admin -lqt | cut -d \| -f 1 | grep -qw process_mining; then
            check_pass "Database 'process_mining' exists"
        else
            check_fail "Database 'process_mining' does not exist"
        fi
        
        # Check PGVector extension
        if docker exec process_mining_db psql -U process_admin -d process_mining -c "SELECT * FROM pg_extension WHERE extname='vector';" 2>/dev/null | grep -q vector; then
            check_pass "PGVector extension is installed"
        else
            check_warn "PGVector extension not found"
        fi
    else
        check_fail "Database is not accepting connections"
    fi
else
    check_info "Database container not running"
fi

# ============================================================================
# 10. CHECK TEST CONFIGURATION
# ============================================================================

print_header "Checking Test Configuration"

if [ -f "pytest.ini" ]; then
    check_pass "pytest.ini exists"
else
    check_fail "pytest.ini not found"
fi

if [ -f "tests/__init__.py" ]; then
    check_pass "tests/__init__.py exists"
else
    check_fail "tests/__init__.py not found"
fi

# Count test files
test_count=$(find tests/ -name "test_*.py" 2>/dev/null | wc -l)
if [ "$test_count" -gt 0 ]; then
    check_pass "Found $test_count test files"
else
    check_warn "No test files found"
fi

# ============================================================================
# 11. SUMMARY
# ============================================================================

print_header "Validation Summary"

echo -e "${BLUE}Results:${NC}"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Passed with $WARNINGS warnings${NC}"
else
    echo -e "${RED}❌ Failed with $ERRORS errors and $WARNINGS warnings${NC}"
fi

echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}Please fix the errors above before proceeding.${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Some warnings detected. Review them before production deployment.${NC}"
    exit 0
else
    echo -e "${GREEN}System is ready! You can now:${NC}"
    echo -e "  1. Start services: ${BLUE}./manage.sh start${NC}"
    echo -e "  2. Run tests: ${BLUE}./run_tests.sh all${NC}"
    echo -e "  3. View docs: ${BLUE}http://localhost:8000/docs${NC}"
    exit 0
fi