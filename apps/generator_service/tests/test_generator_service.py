import pytest
import pandas as pd
from apps.generator_service.generators.baseline import generate_baseline_transactions
from apps.generator_service.validators.data_validator import validate_dataset
from shared.schemas.transaction import DatasetMetadata
from datetime import datetime, timezone

def test_baseline_generator_row_count():
    """Test that the baseline generator returns the exact number of rows requested."""
    df = generate_baseline_transactions(rows=500, seed=42)
    assert len(df) == 500
    assert not df.empty

def test_baseline_generator_no_negative_amounts():
    """Test that the baseline generator never generates negative amounts."""
    df = generate_baseline_transactions(rows=100, seed=42)
    assert (df["amount"] >= 0).all()

def test_validator_catches_negative_amounts():
    """Test that the data validator flags a dataset with negative amounts."""
    # Create a fake dataframe with a negative amount
    bad_df = pd.DataFrame({
        "transaction_id": ["TX_1"],
        "amount": [-50.0],  # Negative!
        "timestamp": [datetime.now(timezone.utc)],
        "is_fraud": [False]
    })
    
    metadata = DatasetMetadata(
        dataset_id="DS_TEST_BAD",
        rows=1,
        fraud_rows=0,
        schema_version="1.0",
        attack_ids=[],
        seed=42,
        generator_version="1.0.0",
        provenance="test",
        created_at=datetime.now(timezone.utc)
    )
    
    report = validate_dataset(bad_df, metadata)
    assert report["schema_valid"] is False
    assert "Found null or negative amounts" in report["quality_issues"]

def test_validator_passes_good_data():
    """Test that the data validator passes a clean, valid dataset."""
    good_df = pd.DataFrame({
        "transaction_id": ["TX_1", "TX_2"],
        "amount": [50.0, 100.0],
        "timestamp": [datetime.now(timezone.utc), datetime.now(timezone.utc)],
        "is_fraud": [False, True],
        "attack_id": [None, "ATO_001"]
    })
    
    metadata = DatasetMetadata(
        dataset_id="DS_TEST_GOOD",
        rows=2,
        fraud_rows=1,
        schema_version="1.0",
        attack_ids=["ATO_001"],
        seed=42,
        generator_version="1.0.0",
        provenance="test",
        created_at=datetime.now(timezone.utc)
    )
    
    report = validate_dataset(good_df, metadata)
    assert report["schema_valid"] is True
    assert report["scenario_fidelity"] is True
    assert len(report["quality_issues"]) == 0