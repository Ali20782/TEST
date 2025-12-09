#!/bin/bash

# Management Script for Process Mining Platform
# Milestone 2: Backend Deployment

set -e

COMPOSE_FILE="docker-compose.yml"
BACKEND_CONTAINER="process_mining_api"
DB_CONTAINER="process_mining_db"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        print_info "Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env and change default passwords!"
        echo ""
        read -p "Press Enter to continue after editing .env..."
    fi
}

# Start services
start() {
    print_header "Starting Services"
    check_env_file
    
    print_info "Building and starting containers..."
    docker-compose up -d --build
    
    print_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Services started successfully!"
        print_info "API: http://localhost:8000"
        print_info "Docs: http://localhost:8000/docs"
        print_info "Health: http://localhost:8000/health"
    else
        print_error "Services started but health check failed"
        print_info "Check logs with: ./manage.sh logs"
    fi
}

# Stop services
stop() {
    print_header "Stopping Services"
    docker-compose down
    print_success "Services stopped"
}

# Restart services
restart() {
    print_header "Restarting Services"
    stop
    sleep 2
    start
}

# View logs
logs() {
    print_header "Viewing Logs"
    if [ -z "$1" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$1"
    fi
}

# Check status
status() {
    print_header "Service Status"
    docker-compose ps
    
    echo ""
    print_info "Checking health endpoint..."
    if curl -f http://localhost:8000/health 2>/dev/null | jq .; then
        print_success "API is healthy"
    else
        print_error "API is not responding"
    fi
}

# Run tests
test() {
    print_header "Running API Tests"
    
    # Check if server is running
    if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_error "Server is not running. Start it first with: ./manage.sh start"
        exit 1
    fi
    
    python -m scripts.test_api
}

# Access database
db_shell() {
    print_header "Database Shell"
    print_info "Connecting to PostgreSQL..."
    docker exec -it $DB_CONTAINER psql -U process_admin -d process_mining
}

# Run database queries
db_stats() {
    print_header "Database Statistics"
    
    docker exec -it $DB_CONTAINER psql -U process_admin -d process_mining -c "
        SELECT 
            'Projects' as table_name, 
            COUNT(*) as count 
        FROM process_mining.projects
        UNION ALL
        SELECT 
            'Event Logs' as table_name, 
            COUNT(*) as count 
        FROM process_mining.event_logs
        UNION ALL
        SELECT 
            'Documents' as table_name, 
            COUNT(*) as count 
        FROM process_mining.documents
        UNION ALL
        SELECT 
            'Document Chunks' as table_name, 
            COUNT(*) as count 
        FROM process_mining.document_chunks;
    "
}

# Clean everything
clean() {
    print_header "Cleaning Up"
    print_warning "This will remove all containers, volumes, and data!"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        print_info "Stopping containers..."
        docker-compose down -v
        
        print_info "Removing uploads..."
        rm -rf uploads/*
        
        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

# Build only
build() {
    print_header "Building Services"
    docker-compose build
    print_success "Build complete"
}

# Install dependencies locally (for development)
install() {
    print_header "Installing Python Dependencies"
    
    if [ ! -d ".venv" ]; then
        print_info "Creating virtual environment..."
        python -m venv .venv
    fi
    
    print_info "Activating virtual environment..."
    source .venv/bin/activate || . .venv/Scripts/activate
    
    print_info "Installing requirements..."
    pip install -r requirements.txt
    pip install -r requirements-backend.txt
    
    print_success "Dependencies installed"
    print_info "Activate venv with: source .venv/bin/activate"
}

# Backup database
backup() {
    print_header "Backing Up Database"
    
    BACKUP_DIR="backups"
    BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    mkdir -p $BACKUP_DIR
    
    print_info "Creating backup..."
    docker exec $DB_CONTAINER pg_dump -U process_admin process_mining > $BACKUP_FILE
    
    print_success "Backup saved to: $BACKUP_FILE"
}

# Show help
show_help() {
    cat << EOF
${BLUE}Process Mining Platform - Management Script${NC}

${GREEN}Usage:${NC}
    ./manage.sh [command]

${GREEN}Commands:${NC}
    ${YELLOW}start${NC}       Start all services
    ${YELLOW}stop${NC}        Stop all services
    ${YELLOW}restart${NC}     Restart all services
    ${YELLOW}status${NC}      Check service status
    ${YELLOW}logs${NC}        View logs (optional: specify service name)
    ${YELLOW}test${NC}        Run API tests
    ${YELLOW}build${NC}       Build Docker images
    ${YELLOW}clean${NC}       Remove all containers and data
    ${YELLOW}install${NC}     Install Python dependencies locally
    
    ${YELLOW}db-shell${NC}    Open PostgreSQL shell
    ${YELLOW}db-stats${NC}    Show database statistics
    ${YELLOW}backup${NC}      Backup database
    
    ${YELLOW}help${NC}        Show this help message

${GREEN}Examples:${NC}
    ./manage.sh start
    ./manage.sh logs backend
    ./manage.sh test
    ./manage.sh db-stats

${GREEN}Quick Start:${NC}
    1. ./manage.sh install    # Install dependencies
    2. Edit .env file         # Configure settings
    3. ./manage.sh start      # Start services
    4. ./manage.sh test       # Run tests

${BLUE}For more info, see MILESTONE2_DEPLOYMENT.md${NC}
EOF
}

# Main script
case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    test)
        test
        ;;
    build)
        build
        ;;
    clean)
        clean
        ;;
    install)
        install
        ;;
    db-shell)
        db_shell
        ;;
    db-stats)
        db_stats
        ;;
    backup)
        backup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac