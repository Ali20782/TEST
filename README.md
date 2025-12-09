# AI-Powered Conversational Process Intelligence Platform

This is the repository for the **AI-Powered Conversational Process Intelligence Platform**.

This project implements a modern system designed to analyse event logs using **Process Mining** techniques and provide **conversational root cause analysis** through a **Retrieval-Augmented Generation (RAG)** pipeline.

## Key Features

* **Process Discovery:** Automatically generates process maps (BPMN) from raw event data using the **pm4py** library.
* **Conversational AI:** Allows users to ask natural language questions about the process, performance, and bottlenecks.
* **Hybrid RAG:** The platform uses a combined vector store (**PGVector**) containing embeddings of both **structured event logs** and **unstructured documentation**.
* **Scalable Architecture:** Built on **FastAPI** (ASGI) for performance and scalability, with asynchronous task processing using **Celery/RabbitMQ**.
* **BPMN Visualisation:** Renders interactive process maps using **bpmn-js** in the frontend.

## System Architecture

For a complete breakdown of component choices, data flow, and scalability design, please consult the full documentation in the /docs directory.

## Datasets

**BPI Challenge 2012**
- **Total Events:** 262,200
- **Total Cases:** 13,087
- **Unique Activities:** 24
- **Date Range:** 2011-10-01 to 2012-03-14

**BPI Challenge 2017**
- **Total Events:** 1,202,267
- **Total Cases:** 31,509
- **Unique Activities:** 26
- **Date Range:** 2016-01-01 to 2017-02-01

**Synthetic_Invoice - Custom generated (Can be adjusted as per need)**
- **Total Events:** 1,242
- **Total Cases:** 200
- **Unique Activities:** 9
- **Date Range:** 2024-01-01 to 2024-04-11

Check the following link to see the current state of the datasets (raw, clean, and synthetic)

- **Link:** https://www.dropbox.com/scl/fo/ipl2xfe5tjn9zdebvkfu4/ADbXh4ZAeYnDbniQEBlwn_Y?rlkey=iykr2nj3dg5r2edgt1w5nzoln&st=fju42nws&dl=0

## Repository Structure

The project is organised into the following top-level directories:

| Directory | Purpose | Key Contents |
| :--- | :--- | :--- |
| **/data** | **Raw, Clean, and Synthetic Data Storage** | `Not pushed to repo` Contains original raw XES/CSV files, intermediate cleaning files, and final event logs used for analysis (e.g., BPI_2012_clean.csv, synthetic_invoice_process.csv). |
| **/scripts** | **Core Execution Code** | Contains all the Python scripts for data handling, process mining, RAG pipeline setup, and API backend services (e.g., data_transformation.py, dataset_validation.py, api_server.py). |
| **/docs** | **Project Documentation** | Stores all architectural diagrams, detailed technical documentation, validation results, and future planning documents (e.g., architecture.md). |

## Folder Structure

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
│   ├── ...
├── docs/ (Documentation and reports for the project)
|   ├── data_validation/
|   |    └── ...
│   └── ...
├── .venv/ (virtual environment)
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

* Python (3.10 or newer)

### Setup

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
    python -m "scripts.data_transformation"

    # 2. Run synthetic data generation
    python -m "scripts.synthetic_data_generator"
    
    # 3. Run process mining validation on all datasets
    python -m "scripts.dataset_validation"
    ```
    (The validation results, including process maps and a report, will be saved to the /validation directory.)


## Documentation

For detailed information regarding the implementation, consult the documents in the /docs directory.

