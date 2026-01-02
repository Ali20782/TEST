

echo "=========================================="
echo "Milestone 2 - Deployment and Ingestion Tests"
echo "=========================================="

# Check if Docker containers are running
echo ""
echo "Checking Docker containers..."
if ! docker ps | grep -q "process_mining_backend"; then
    echo "❌ Backend container not running!"
    echo "   Start with: docker-compose up -d"
    exit 1
fi

if ! docker ps | grep -q "process_mining_db"; then
    echo "❌ Database container not running!"
    echo "   Start with: docker-compose up -d"
    exit 1
fi

echo "✅ Containers are running"

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 5

# Check health endpoint
echo ""
echo "Checking API health..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$response" -eq 200 ]; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed (HTTP $response)"
    exit 1
fi

# Run tests
echo ""
echo "Running backend (Milestone 2) tests..."
echo "=========================================="
pytest scripts/tests/test_Milestone_2.py -v --tb=short -s

# Capture exit code
TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
else
    echo "❌ SOME TESTS FAILED"
fi
echo "=========================================="

exit $TEST_EXIT_CODE
