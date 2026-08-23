import pandas as pd
import os
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata
from apps.generator_service.generators.baseline import generate_baseline_transactions

MODEL_PATH = "data/synthetic/ctgan_model.pkl"

def train_ctgan_model(rows=2000, seed=42):   #update rows=10000 if needed
    """Trains a CTGAN model on baseline data and saves it."""
    print(f"Generating {rows} baseline rows for CTGAN training...")
    df = generate_baseline_transactions(rows=rows, seed=seed)
    
    # Drop columns CTGAN struggles with
    df_train = df.drop(columns=["timestamp", "transaction_id", "attack_id", "is_fraud"])
    
    metadata = SingleTableMetadata()
    metadata.detect_from_dataframe(df_train)
    
    print("Training CTGAN model (reduced epochs for speed)...")
    # Reduce epochs to 50 for a fast hackathon demo (default is 300)
    model = CTGANSynthesizer(metadata, epochs=50)
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