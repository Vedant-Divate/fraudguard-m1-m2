from fastapi import FastAPI
from uuid import uuid4
from datetime import datetime, timezone
import pandas as pd
from shared.schemas.envelope import EnvelopeResponse, EnvelopeRequest
from shared.schemas.transaction import GenerationRequest, DatasetMetadata
from apps.generator_service.generators.baseline import generate_baseline_transactions
from apps.generator_service.generators.attack_conditioner import generate_attack_transactions
from apps.generator_service.storage import save_dataset

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
    
    # Calculate row counts
    fraud_rows_count = int(req_data.rows * req_data.fraud_ratio)
    legit_rows_count = req_data.rows - fraud_rows_count
    
    # 1. Generate Legitimate Transactions
    df_legit = generate_baseline_transactions(rows=legit_rows_count, seed=req_data.seed)
    
    # 2. Generate Fraud Transactions (if requested)
    df_fraud = pd.DataFrame()
    if fraud_rows_count > 0 and req_data.attack_ids:
        attack_id = req_data.attack_ids[0] 
        df_fraud = generate_attack_transactions(attack_id, rows=fraud_rows_count, seed=req_data.seed + 1)
        
    # 3. Combine and shuffle
    df_combined = pd.concat([df_legit, df_fraud]).sample(frac=1, random_state=req_data.seed).reset_index(drop=True)
    
    dataset_id = f"DS_{uuid4().hex[:8]}"
    
    # Create the metadata object first
    metadata = DatasetMetadata(
        dataset_id=dataset_id,
        rows=len(df_combined),
        fraud_rows=len(df_fraud),
        schema_version="1.0",
        attack_ids=req_data.attack_ids if len(df_fraud) > 0 else [],
        seed=req_data.seed,
        generator_version="1.0.0",
        provenance="baseline_plus_attacks",
        created_at=datetime.now(timezone.utc)
    )
    
    # 4. Save to Parquet and Manifest
    save_dataset(df_combined, metadata)
    
    return EnvelopeResponse(
        request_id=payload.request_id,
        timestamp=datetime.now(timezone.utc),
        data=metadata
    )