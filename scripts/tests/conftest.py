"""
Pytest Configuration and Shared Fixtures
Place this file at: scripts/tests/conftest.py
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to Python path - CRITICAL for imports to work
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Verify the path was added
print(f"Added to sys.path: {project_root}")

# Test markers
pytest_markers = {
    'unit': 'Unit tests',
    'integration': 'Integration tests',
    'slow': 'Slow running tests',
    'database': 'Tests requiring database',
    'api': 'API endpoint tests',
    'embedding': 'Embedding model tests'
}


def pytest_configure(config):
    """Configure pytest with custom markers"""
    for marker, description in pytest_markers.items():
        config.addinivalue_line("markers", f"{marker}: {description}")


@pytest.fixture(scope="session")
def test_data_dir():
    """Test data directory"""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def sample_event_data():
    """Sample event log data"""
    return {
        'case_id': ['C1', 'C1', 'C2', 'C2'],
        'activity': ['Start', 'End', 'Start', 'End'],
        'timestamp': [
            '2024-01-01T10:00:00',
            '2024-01-01T11:00:00',
            '2024-01-01T10:30:00',
            '2024-01-01T11:30:00'
        ],
        'resource': ['User1', 'User1', 'User2', 'User2']
    }


@pytest.fixture(scope="session")
def api_base_url():
    """Base URL for API tests"""
    return os.getenv('API_BASE_URL', 'http://localhost:8000')


@pytest.fixture(autouse=True)
def reset_test_env():
    """Reset test environment before each test"""
    # Clear any test-specific environment variables
    test_vars = [k for k in os.environ.keys() if k.startswith('TEST_')]
    for var in test_vars:
        os.environ.pop(var, None)
    
    yield
    
    # Cleanup after test
    pass


# Pytest configuration options
def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--integration-only",
        action="store_true",
        default=False,
        help="Run only integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options"""
    if not config.getoption("--slow"):
        skip_slow = pytest.mark.skip(reason="need --slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    if config.getoption("--integration-only"):
        skip_unit = pytest.mark.skip(reason="--integration-only specified")
        for item in items:
            if "integration" not in item.keywords:
                item.add_marker(skip_unit)