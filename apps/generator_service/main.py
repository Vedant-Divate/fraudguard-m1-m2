from fastapi import FastAPI
from uuid import uuid4
from datetime import datetime, timezone
from shared.schemas.envelope import EnvelopeResponse, EnvelopeRequest
from shared.schemas.transaction import GenerationRequest, DatasetMetadata
from apps.generator_service.generators.baseline import generate_baseline_transactions

app = FastAPI(title="FraudGuard 360 - Synthetic Generator", docs_url="/docs")

def generate_request_id() -> str:
    return f"REQ_{uuid4().hex[:12]}"

@app.get("/health")
async def health():
    return EnvelopeResponse(
        request_id=generate_request_id(),
        timestamp=datetime.now(timezone.utc),
        data={"status": "healthy"}
    )

@app.post("/api/v1/generator/transactions")
async def generate_transactions(payload: EnvelopeRequest):
    req_data = GenerationRequest(**payload.data)
    
    # For now, we just generate the baseline (legitimate) transactions
    # Later, we will split this into legit + fraud based on fraud_ratio and attack_ids
    df = generate_baseline_transactions(rows=req_data.rows, seed=req_data.seed)
    
    dataset_id = f"DS_{uuid4().hex[:8]}"
    
    # TODO: Save to Parquet in data/synthetic/{dataset_id}/transactions.parquet
    
    return EnvelopeResponse(
        request_id=payload.request_id,
        timestamp=datetime.now(timezone.utc),
        data=DatasetMetadata(
            dataset_id=dataset_id,
            rows=len(df),
            fraud_rows=0, # 0 for now, until we add the attack conditioner
            schema_version="1.0",
            attack_ids=req_data.attack_ids,
            seed=req_data.seed,
            generator_version="1.0.0",
            provenance="baseline_only",
            created_at=datetime.now(timezone.utc)
        )
    )