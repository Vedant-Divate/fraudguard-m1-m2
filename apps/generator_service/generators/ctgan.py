import pandas as pd
import os
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
from apps.generator_service.generators.baseline import generate_baseline_transactions

MODEL_PATH = "data/synthetic/ctgan_model.pkl"

def train_ctgan_model(rows=10000, seed=42):
    """Trains a CTGAN model on baseline data and saves it."""
    print(f"Generating {rows} baseline rows for CTGAN training...")
    df = generate_baseline_transactions(rows=rows, seed=seed)
    
    # Drop columns CTGAN struggles with for MVP
    df_train = df.drop(columns=["timestamp", "transaction_id"])
    
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df_train)
    
    print("Training CTGAN model (this may take a minute)...")
    model = CTGANSynthesizer(metadata)
    model.fit(df_train)
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)
    print("CTGAN model trained and saved!")
    return model

def generate_ctgan_rows(rows: int, seed: int = 42):
    """Loads the trained CTGAN model and generates rows."""
    if not os.path.exists(MODEL_PATH):
        train_ctgan_model()
        
    model = CTGANSynthesizer.load(MODEL_PATH)
    sampled = model.sample(num_rows=rows)
    
    # Add back the required columns we dropped
    sampled["transaction_id"] = [f"TX_CTGAN_{i}" for i in range(rows)]
    sampled["timestamp"] = pd.Timestamp.now()
    sampled["attack_id"] = None
    sampled["is_fraud"] = False
    
    # Ensure amount is non-negative
    sampled["amount"] = sampled["amount"].clip(lower=0.0)
    
    return sampled