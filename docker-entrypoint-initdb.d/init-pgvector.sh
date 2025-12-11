#!/bin/bash
# This script runs when the PostgreSQL container starts for the first time.
# It uses the PostgreSQL package manager (apt) to install the necessary PGVector package.

echo "Installing postgresql-15-pgvector..."
apt-get update && apt-get install -y postgresql-15-pgvector

echo "Running standard setup on database: $POSTGRES_DB"

# The extension is enabled in the Python api_server.py script 
# when the backend connects (via database.py -> setup_db()).
# The installation is now done, which is the key step.