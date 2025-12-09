#!/bin/bash

echo "🚀 Setting up Process Mining Platform..."
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/raw data/clean data/synthetic
mkdir -p uploads/structured uploads/unstructured
mkdir -p logs
mkdir -p sql

echo "✅ Directories created"
echo ""

# Make sure .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found, creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        # Create .env with default values
        cat > .env << 'EOF'
POSTGRES_USER=process_admin
POSTGRES_PASSWORD=ProcessMining2024!
POSTGRES_DB=process_mining
DATABASE_URL=postgresql://process_admin:ProcessMining2024!@postgres:5432/process_mining
APP_ENV=development
LOG_LEVEL=info
MAX_UPLOAD_SIZE=100
ALLOWED_EXTENSIONS=csv,xlsx,xls,txt,docx,pdf
EMBEDDING_MODEL=all-MiniLM-L6-v2
SECRET_KEY=dev-secret-key-change-in-production-12345678
EOF
    fi
    echo "✅ .env file created"
fi

echo ""
echo "📦 Building Docker containers..."
docker compose build

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready (30 seconds)..."
sleep 30

echo ""
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is running at http://localhost:8000"
    echo "✅ Swagger docs available at http://localhost:8000/docs"
else
    echo "⚠️  API is starting... Check logs with: docker compose logs backend"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 PostgreSQL Credentials:"
echo "   Username: process_admin"
echo "   Password: ProcessMining2024!"
echo "   Database: process_mining"
echo "   Port: 5432"
echo ""
echo "📝 Useful commands:"
echo "   View logs: docker compose logs -f"
echo "   Stop services: docker compose down"
echo "   Restart: docker compose restart"
echo "   Database shell: docker exec -it process_mining_db psql -U process_admin -d process_mining"
echo ""