import os
import json
from pandas import DataFrame
from shared.schemas.transaction import DatasetMetadata

def save_dataset(df: DataFrame, metadata: DatasetMetadata):
    """Saves the DataFrame to Parquet and the metadata to a JSON manifest."""
    
    # 1. Define the folder path (Absolute path based on this file's location)
    # __file__ is apps/generator_service/storage.py
    # We go up two levels to get to the project root, then into data/synthetic
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dataset_dir = os.path.join(project_root, "data", "synthetic", metadata.dataset_id)
    os.makedirs(dataset_dir, exist_ok=True)
    
    # 2. Save the Parquet file
    parquet_path = os.path.join(dataset_dir, "transactions.parquet")
    df.to_parquet(parquet_path, index=False)
    
    # 3. Save the manifest JSON
    manifest_path = os.path.join(dataset_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        # Convert Pydantic model to dict, then to JSON
        json.dump(metadata.model_dump(mode="json"), f, indent=2)
        
    print(f"Dataset successfully saved to: {dataset_dir}")
    return parquet_path