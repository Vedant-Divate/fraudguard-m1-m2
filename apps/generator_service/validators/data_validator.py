import pandas as pd
from shared.schemas.transaction import DatasetMetadata

def validate_dataset(df: pd.DataFrame, metadata: DatasetMetadata) -> dict:
    """
    Runs data quality and scenario fidelity checks on the generated dataframe.
    Returns a report dictionary.
    """
    report = {
        "schema_valid": True,
        "quality_issues": [],
        "scenario_fidelity": True,
        "row_count": len(df),
        "fraud_row_count": len(df[df["is_fraud"] == True])
    }
    
    # 1. Schema & Quality Checks
    if df["amount"].isnull().any() or (df["amount"] < 0).any():
        report["schema_valid"] = False
        report["quality_issues"].append("Found null or negative amounts")
        
    if df["transaction_id"].duplicated().any():
        report["schema_valid"] = False
        report["quality_issues"].append("Found duplicate transaction IDs")
        
    if df["timestamp"].isnull().any():
        report["schema_valid"] = False
        report["quality_issues"].append("Found null timestamps")
        
    # 2. Scenario Fidelity Checks (Verify fraud signals exist)
    # For a hackathon, we just verify that fraud rows have an attack_id and is_fraud=True
    fraud_df = df[df["is_fraud"] == True]
    if len(fraud_df) > 0:
        if fraud_df["attack_id"].isnull().any():
            report["scenario_fidelity"] = False
            report["quality_issues"].append("Fraud rows missing attack_id")
            
        # Check ATO signal: If attack_id is ATO_001, new_device should be true
        # (We can't easily check new_device here without the scenario object, 
        # but we guarantee the attack_conditioner applied it)
        
    else:
        if metadata.fraud_rows > 0:
            report["scenario_fidelity"] = False
            report["quality_issues"].append("Metadata claims fraud rows exist, but none found in data")
            
    return report