from fastapi import FastAPI
from uuid import uuid4
from datetime import datetime, timezone
import pandas as pd
from shared.schemas.envelope import EnvelopeResponse, EnvelopeRequest
from shared.schemas.transaction import GenerationRequest, DatasetMetadata
from apps.generator_service.generators.baseline import generate_baseline_transactions
from apps.generator_service.generators.attack_conditioner import generate_attack_transactions
from apps.generator_service.storage import save_dataset
from apps.generator_service.validators.data_validator import validate_dataset
from fastapi import HTTPException
import os
import json     

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
    
    # 4. Run Validators
    validation_report = validate_dataset(df_combined, metadata)
    if not validation_report["schema_valid"]:
        raise HTTPException(status_code=500, detail=f"Data validation failed: {validation_report['quality_issues']}")
        
    # 5. Save to Parquet and Manifest
    save_dataset(df_combined, metadata)
    
    # 6. Return response with validation report included
    response_data = metadata.model_dump()
    response_data["validation_report"] = validation_report
    
    return EnvelopeResponse(
        request_id=payload.request_id,
        timestamp=datetime.now(timezone.utc),
        data=response_data
    )

@app.get("/api/v1/generator/dataset/{dataset_id}")
async def get_dataset(dataset_id: str):
    # Look for the manifest file we saved earlier
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    manifest_path = os.path.join(project_root, "data", "synthetic", dataset_id, "manifest.json")
    
    if not os.path.exists(manifest_path):
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    with open(manifest_path, "r") as f:
        metadata = json.load(f)
        
    return EnvelopeResponse(
        request_id=generate_request_id(),
        timestamp=datetime.now(timezone.utc),
        data=metadata
    )