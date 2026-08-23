# FraudGuard 360 - Red Team Engine (M1 & M2)
**Mastercard Innovation Challenge @ GFF 2026**

This repository contains the **Threat Intelligence & Red Team (M1)** and **Synthetic Data Generator (M2)** modules for the FraudGuard 360 platform.

It forms the front half of a closed-loop AI system that uses Large Language Models to discover emerging payment-fraud patterns, mutates them into harder variants, and generates high-fidelity synthetic transaction data to train and stress-test the Blue Team detection models.

## 🏛️ Architecture & Data Flow

1. **Threat Intelligence (M1):** A LangGraph agent uses an LLM (Groq/Llama 3.3) to propose novel attack scenarios in strict JSON. A Pydantic schema validator ensures structural integrity.
2. **Scenario Registry:** Validated scenarios are stored in PostgreSQL with full versioning and provenance tracking.
3. **Mutation Engine:** Applies rule-based operators (e.g., `bump_velocity`, `swap_device`) to existing scenarios to create "hard negative" variants.
4. **Synthetic Generator (M2):** Fetches scenarios from M1 via HTTP, generates a baseline of realistic normal transactions (Pandas/NumPy), and distorts a portion of them to exhibit the exact fraud signals defined in the scenario.
5. **Data Vault:** The final labeled dataset is validated for schema/fidelity, then saved to disk as `.parquet` files alongside a `manifest.json` for downstream ML training (M3/M4).

## 🛠️ Tech Stack

- **API Framework:** FastAPI, Pydantic v2
- **AI/Agents:** LangGraph, LangChain, Groq (Llama 3.3)
- **Database:** PostgreSQL, SQLAlchemy
- **Data Engine:** Pandas, NumPy, PyArrow (Parquet)
- **Infrastructure:** Docker, Docker Compose

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker Desktop (for PostgreSQL)

### 1. Environment Setup

Create a virtual environment and install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your Groq API key (get a free one at [console.groq.com](https://console.groq.com)):

```powershell
cp .env.example .env
# Edit .env to add your GROQ_API_KEY
```

### 3. Start the Database

Start the local PostgreSQL database via Docker:

```powershell
docker compose up -d postgres
```

### 4. Seed the Database (M1)

Populate the database with 12 hand-crafted baseline attack scenarios:

```powershell
py -m apps.threat_service.seed
```

### 5. Run the Services

Open two terminal windows to run both microservices:

**Terminal 1 (Member 1 - Port 8001):**

```powershell
uvicorn apps.threat_service.main:app --reload --port 8001
```

**Terminal 2 (Member 2 - Port 8002):**

```powershell
uvicorn apps.generator_service.main:app --reload --port 8002
```

## 📚 API Endpoints

### Member 1: Threat Intelligence (`http://localhost:8001`)

- `POST /api/v1/attacks/discover`: Uses LLM to generate a novel attack scenario.
- `GET /api/v1/attacks`: Lists all approved scenarios in the registry.
- `GET /api/v1/attacks/{attack_id}`: Fetches a specific scenario.
- `POST /api/v1/attacks/mutate`: Applies mutation operators to create harder variants.

### Member 2: Synthetic Generator (`http://localhost:8002`)

- `POST /api/v1/generator/transactions`: Generates mixed legitimate/fraud transactions and saves to Parquet.
- `GET /api/v1/generator/dataset/{dataset_id}`: Retrieves metadata for a generated dataset.

## 🧪 Testing

Unit tests are written using `pytest`. To run the tests for both modules:

```powershell
pytest apps/threat_service/tests/
pytest apps/generator_service/tests/
```

## 🐳 Docker Deployment

To run the entire stack (Postgres + M1 API + M2 API) in isolated containers:

```powershell
docker compose up --build
```

*Note: Ensure your `.env` file is populated before building.*

## Git Branch Workflow

Save the README to both feature branches:

```bash
# 1. Commit to synthetic-generator
git add .
git commit -m "docs: add professional README with architecture and run instructions"
git push origin feature/synthetic-generator

# 2. Switch to the threat branch
git checkout feature/threat-intelligence

# 3. Bring the README over from the generator branch
git checkout feature/synthetic-generator -- README.md

# 4. Commit to threat-intelligence
git add .
git commit -m "docs: add professional README with architecture and run instructions"
git push origin feature/threat-intelligence
```
