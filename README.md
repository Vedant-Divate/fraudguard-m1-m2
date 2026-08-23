# FraudGuard 360

**Closed-loop Red Team / Blue Team AI system for payment fraud detection.**
Built for the Mastercard Innovation Challenge @ GFF 2026.

---

## What it does

FraudGuard 360 identifies emerging payment-fraud patterns, generates safe high-fidelity synthetic scenarios, detects them with a low-latency ML pipeline, and feeds detection gaps back into the red team for continuous hardening.

**Core loop:** `Identify → Generate → Defend → Learn`

> **Important:** The LLM / red-team generation layer is kept **out of the live authorization path**. Real-time decisions use pre-trained, validated, low-latency models and deterministic decision logic. GenAI is used **offline/nearline only** — for threat discovery, scenario generation, mutation, analysis, and model hardening.

---

## Architecture

```
Threat Intelligence → Attack Scenarios → Synthetic Data Vault →
Feature & Graph Layer → ML Models → Decision Engine →
Live-style Risk API → Feedback/Drift → New Attack Scenarios
```

| Path | Components | Latency Goal | Purpose |
|---|---|---|---|
| **Real-time** | Feature service + XGBoost/LightGBM + rules + decision engine | Sub-100ms (prototype) | Risk score + transaction action |
| **Nearline** | Graph refresh + monitoring + feedback aggregation | Seconds/minutes | Update risk context, detect drift |
| **Offline** | LLM agents + synthetic generator + retraining | Minutes/hours | Discover & simulate new attack patterns |

---

## Team & Modules

| Owner | Module | Core Tech | Hands off |
|---|---|---|---|
| Project Lead | Architecture, contracts, integration, CI/CD, demo | GitHub Actions, Docker, FastAPI, PostgreSQL | Integrated system |
| Member 1 | Threat Intelligence & Red Team | Python, LangGraph, LLM API, Pydantic | Attack JSON + scenarios |
| Member 2 | Synthetic Data Generator | Python, Pandas, NumPy, SDV/CTGAN | Datasets + generator API |
| Member 3 | Features & Graph | Pandas, NetworkX, Neo4j (optional) | Feature API + feature schema |
| Member 4 | Fraud Detection ML | XGBoost, LightGBM, SHAP, MLflow | Model artifact + prediction API |
| Member 5 | Real-time Risk & Decision | FastAPI, Redis, Kafka, Pydantic | Risk API + decision engine |
| Member 6 | Feedback, Monitoring & UI | MLflow, Evidently, Prometheus, Grafana, React | Monitoring + dashboard |

---

## Repository Structure

```
FraudGuard360/
├── apps/
│   ├── threat_service/       # Member 1
│   ├── generator_service/    # Member 2
│   ├── feature_service/      # Member 3
│   ├── model_service/        # Member 4
│   ├── risk_service/         # Member 5
│   └── monitoring_service/   # Member 6
├── frontend/
├── shared/
│   ├── schemas/
│   ├── logging/
│   └── config/
├── data/
│   ├── synthetic/
│   └── fixtures/
├── models/
├── tests/
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js (for frontend/dashboard)

### Run the full stack locally
```bash
git clone https://github.com/<org>/FraudGuard360.git
cd FraudGuard360
cp .env.example .env
docker compose up --build
```

Each service exposes its own OpenAPI docs at `/docs` once running.

---

## Shared API Contract

All modules communicate over JSON/HTTP. Every request carries a `request_id` and schema version.

**Request**
```json
{
  "request_id": "REQ_001",
  "timestamp": "2026-08-21T12:30:00Z",
  "schema_version": "1.0",
  "data": {}
}
```

**Response**
```json
{
  "request_id": "REQ_001",
  "status": "success",
  "data": {},
  "error": null
}
```

**Error**
```json
{
  "request_id": "REQ_001",
  "status": "error",
  "data": null,
  "error": { "code": "VALIDATION_ERROR", "message": "amount must be non-negative" }
}
```

### Canonical Transaction Schema

| Field | Type | Required | Description |
|---|---|---|---|
| transaction_id | string | Yes | Unique synthetic transaction ID |
| customer_id | string | Yes | Synthetic customer ID |
| merchant_id | string | Yes | Synthetic merchant ID |
| amount | float | Yes | Transaction amount |
| currency | string | Yes | Currency code |
| timestamp | ISO-8601 | Yes | Transaction time |
| channel | enum | Yes | CARD/UPI/WALLET/P2P etc. |
| device_id | string | Recommended | Synthetic device ID |
| location | object | Recommended | Coarse location context |
| merchant_category | string | Recommended | Merchant category |
| attack_id | string/null | Yes | Null for legitimate; scenario ID for attacks |
| is_fraud | boolean | Yes | Ground-truth label (synthetic data only) |

---

## Module API Summary

| Module | Key Endpoints |
|---|---|
| Threat Intelligence | `POST /api/v1/attacks/discover`, `GET /api/v1/attacks`, `GET /api/v1/attacks/{id}`, `POST /api/v1/attacks/mutate` |
| Synthetic Generator | `POST /api/v1/generator/transactions`, `POST /api/v1/generator/scenario`, `GET /api/v1/generator/dataset/{id}` |
| Features & Graph | `POST /api/v1/features/extract`, `POST /api/v1/graph/risk`, `GET /api/v1/features/schema` |
| Detection ML | `POST /api/v1/model/predict`, `GET /api/v1/model/info`, `GET /api/v1/model/explain/{id}` |
| Risk API | `POST /api/v1/risk/score`, `POST /api/v1/decision`, `GET /api/v1/risk/{id}`, `GET /api/v1/health`, `POST /api/v1/feedback` |
| Monitoring | `POST /api/v1/feedback`, `GET /api/v1/model/metrics`, `GET /api/v1/drift`, `GET /api/v1/system/metrics` |

Full request/response contracts and per-module details live in each service's own README under `apps/<service>/`.

---

## Development Workflow

- No direct pushes to `main`. Work happens on `feature/<module-name>` branches.
- A feature merges only after: unit tests pass, API contract checks pass, and a reviewer approves.
- Each module owner maintains their own README with: setup instructions, API docs, test command, sample I/O, and known limitations.

**Branches:**
```
main
feature/threat-intelligence
feature/synthetic-generator
feature/feature-engine
feature/detection-model
feature/risk-engine
feature/monitoring-dashboard
```

---

## Testing Strategy

| Layer | Purpose |
|---|---|
| Unit tests | Each member's deterministic functions |
| Contract tests | API request/response schema validation |
| Integration tests | Module-to-module calls with realistic payloads |
| Load tests | Latency/throughput of the real-time risk service |
| Model tests | Predictive quality on a locked test set |
| Drift tests | Feature distribution shift → monitoring reaction |
| Failure tests | Dependency down → safe failure or fallback |

---

## Non-Goals

- No connection to real customer payment credentials or live authorization systems.
- No automation of real fraud, credential theft, phishing, or unauthorized transactions.
- No generative LLM in the synchronous authorization path.
- No production-readiness claims based solely on offline metrics.

---

## Roadmap (18-Day Execution Plan)

| Days | Focus | Milestone |
|---|---|---|
| 1–2 | Schemas, skeletons, baseline model | Repo + API contracts fixed |
| 3–5 | M1–M4 core pipeline; M5/M6 skeletons | First prediction demo |
| 6–8 | LLM mutation, CTGAN, graph, SHAP, Redis/Kafka, monitoring | Red-team → blue-team flow works |
| 9–11 | Feedback + retraining loop | Closed-loop demo |
| 12–14 | Load, robustness, drift, failure handling | Operational feasibility evidence |
| 15–16 | Dashboard, demo storyline, docs | One-click demo flow |
| 17–18 | Final QA and submission | Stable final build |

---

## Final Acceptance Checklist

- [ ] All six members pushed module code to feature branches
- [ ] Every API has OpenAPI docs + example request/response
- [ ] Every module has a local test command + README section
- [ ] No production credentials or real customer data used
- [ ] Attack scenarios versioned and traceable to generated datasets
- [ ] Model version + feature schema logged with every prediction
- [ ] Risk API latency benchmarked under synthetic load
- [ ] Fallback behavior demonstrated on model dependency failure
- [ ] Drift detection triggered with a controlled test
- [ ] Feedback loop created at least one new attack mutation in demo
- [ ] Full system starts from a reproducible Docker Compose environment
- [ ] Final presentation separates prototype results from production claims

---

## License

TBD

## Team

Project built for the Mastercard Innovation Challenge @ GFF 2026.
