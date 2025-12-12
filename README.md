# AI-Powered Conversational Process Intelligence Platform

This is the repository for the **AI-Powered Conversational Process Intelligence Platform**.

This project implements a modern system designed to analyse event logs using Process Mining techniques and provide conversational root cause analysis through a Retrieval-Augmented Generation (RAG) pipeline.

## Key Features

  * **Process Discovery:** Automatically generates process maps (BPMN) from raw event data using the **pm4py** library.
  * **Conversational AI:** Allows users to ask natural language questions about the process, performance, and bottlenecks.
  * **Hybrid RAG:** The platform uses a combined vector store (**PGVector**) containing embeddings of both **structured event logs** and **unstructured documentation**.
  * **Scalable Architecture:** Built on **FastAPI** (ASGI) for performance and scalability, with asynchronous task processing using **Celery/RabbitMQ**.
  * **BPMN Visualisation:** Renders interactive process maps using **bpmn-js** in the frontend.

-----
## Milestone 1: Architecture, Environment Setup and Data Prep

### System Architecture

For a complete breakdown of component choices, data flow, and scalability design, please consult the full documentation in the /docs directory.

### Datasets

**BPI Challenge 2012**

  * **Total Events:** 262,200
  * **Total Cases:** 13,087
  * **Unique Activities:** 24
  * **Date Range:** 2011-10-01 to 2012-03-14

**BPI Challenge 2017**

  * **Total Events:** 1,202,267
  * **Total Cases:** 31,509
  * **Unique Activities:** 26
  * **Date Range:** 2016-01-01 to 2017-02-01

**Synthetic\_Invoice - Custom generated (Can be adjusted as per need)**

  * **Total Events:** 1,242
  * **Total Cases:** 200
  * **Unique Activities:** 9
  * **Date Range:** 2024-01-01 to 2024-04-11

Check the following link to see the current state of the datasets (raw, clean, and synthetic)

  * **Link:** [https://www.dropbox.com/scl/fo/ipl2xfe5tjn9zdebvkfu4/ADbXh4ZAeYnDbniQEBlwn](https://www.google.com/search?q=https://www.dropbox.com/scl/fo/ipl2xfe5tjn9zdebvkfu4/ADbXh4ZAeYnDbniQEBlwn\_Yrlkey=iykr2nj3dg5r2edgt1w5nzoln\&st=fju42nws\&dl=0)

### Repository Structure

The project is organised into the following top-level directories:

| Directory | Purpose | Key Contents |
| :--- | :--- | :--- |
| **/data** | **Raw, Clean, and Synthetic Data Storage** | `Not pushed to repo` Contains original raw XES/CSV files, intermediate cleaning files, and final event logs used for analysis (e.g., BPI\_2012\_clean.csv, synthetic\_invoice\_process.csv). |
| **/scripts** | **Core Execution Code** | Contains all the Python scripts for data handling, process mining, RAG pipeline setup, and API backend services (e.g., data\_transformation.py, dataset\_validation.py, api\_server.py). |
| **/docs** | **Project Documentation** | Stores all architectural diagrams, detailed technical documentation, validation results, and future planning documents (e.g., architecture.md). |

### Folder Structure

```
AI-Powered-Conversational-Process-Int-Platform/
├── data/ (All datasets are stored here)
│   ├── clean/ (cleaned data)
│   │   └── ...
│   ├── raw/ (raw unclean data)
│   │   └── ...
│   └── synthetic/ (All synthetic data)
│       └── ...
├── scripts/ (All code files is stored ehre)
|   ├── tests/ (Contains pytest scripts)
|   ├── data_scripts/ (scripts for cleaning and generating real/synthetic data)
│   ├── ...
├── docs/ (Documentation and reports for the project)
|   ├── architecture/ (Contains details about the architecture of the system)
|   ├── data_validation/
|   |    └── ...
│   └── ...
├── .venv/ (virtual environment)
├── .env (Environment variables)
├── .gitignore
├── repoRoot.py (Returns repository root - used by other processes)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

-----

### Environment Setup and Data Prep

This milestone focuses on setting up the core development environment and preparing the necessary datasets.

#### Prerequisites

  * Python (3.10 or newer)

#### Setup

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/AliDev110/AI-Powered-Conversational-Process-Int-Platform
    ```

2.  **Set up Environment:**

    ```bash
    # Create and activate a virtual environment (recommended)
    python -m venv .venv
    .\.venv\Scripts\activate  # Windows
    # source .venv/bin/activate  # macOS/Linux

    # Install Python dependencies
    pip install -r requirements.txt
    ```

3.  **Run Data Transformation and Validation:**
    Execute the scripts in order to prepare the data and verify the event logs.

    ```bash
    # 1. Transform raw data into clean event logs
    python -m "scripts.data_scripts.data_transformation"

    # 2. Run synthetic data generation
    python -m "scripts.data_scripts.synthetic_data_generator"

    # 3. Run process mining validation on all datasets
    python -m "scripts.data_scripts.dataset_validation"
    ```

    (The validation results, including process maps and a report, will be saved to the **/docs/data_validation** directory.)

-----

## Milestone 2: Deployment & Ingestion

This milestone delivers a containerized FastAPI backend with PostgreSQL and PGVector, implementing ingestion APIs for both structured and unstructured data.

### Deliverables ✅

  - ✅ Running backend stack (FastAPI + PostgreSQL + PGVector)
  - ✅ Health check endpoint
  - ✅ Docker Compose file for easy deployment
  - ✅ Structured data ingestion (CSV, XLSX)
  - ✅ Unstructured data ingestion (TXT, DOCX)
  - ✅ Swagger/OpenAPI documentation
  - ✅ Git versioning

### 1\. Setup Environment

Create **.env** file with database credentials:

```bash
# Database Configuration
DB_HOST=db
DB_PORT=5432
DB_NAME=process_db
DB_USER=user
DB_PASSWORD=secret_password

# AI Configuration (for later milestones)
GEMINI_API_KEY=
```

### 2\. Start Services

```bash
# Build and start containers
docker-compose --env-file .env up --build -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 3\. Verify Deployment

Check health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "database": "connected",
  "api_version": "1.0.0"
}
```

### 4\. Access API Documentation

Open browser: http://localhost:8000/docs

### API Endpoints

| Endpoint | Method | Purpose | File Types | Required/Key Columns |
| :--- | :--- | :--- | :--- | :--- |
| /health | **GET** | Check API and database status | N/A | N/A |
| /ingest/structured | **POST** | Upload structured event logs | CSV/XLSX | case_id, activity, timestamp |
| /ingest/unstructured | **POST** | Upload documentation | TXT/DOCX | Text is chunked and stored with embeddings (Embeddings to be finalised in next milestone) |

### Database Schema

| Table | Purpose | Key Columns |
| :--- | :--- | :--- |
| **event\_logs** | Stores structured event log data | case_id, activity, timestamp, resource, cost, location, product_type |
| **documents** | Stores document metadata | filename, file_type, content_text |
| **document\_chunks** - To be finalised in next milestone | Stores text chunks with embeddings | document_id, chunk_index, chunk_text, embedding (vector) |

### Testing

#### Run Milestone 2 Tests

```bash
# Use Git Bash
./scripts/tests/run_tests.sh
```

### Troubleshooting

#### Container keeps restarting

Check logs:

```bash
docker-compose logs backend
```

Possible issues:

  - Database not ready → Wait 30 seconds after startup
  - Missing environment variables → Check .env file
  - Port already in use → Change port in docker-compose.yml

#### Reset everything

```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Rebuild and restart
docker-compose up --build -d
```
