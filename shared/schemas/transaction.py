from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ChannelEnum(str, Enum):
    CARD = "CARD"
    UPI = "UPI"
    WALLET = "WALLET"
    P2P = "P2P"
    BNPL = "BNPL"

class Location(BaseModel):
    country: str
    city: str

class Transaction(BaseModel):
    transaction_id: str
    customer_id: str
    merchant_id: str
    amount: float = Field(ge=0.0) # Must be non-negative
    currency: str = "USD"
    timestamp: datetime
    channel: ChannelEnum
    device_id: Optional[str] = None
    location: Optional[Location] = None
    merchant_category: Optional[str] = None
    attack_id: Optional[str] = None # Null for legitimate, scenario ID for attack
    is_fraud: bool = False

class GenerationRequest(BaseModel):
    rows: int = Field(default=1000, gt=0)
    fraud_ratio: float = Field(default=0.05, ge=0.0, le=1.0)
    attack_ids: list[str] = []
    seed: int = 42
    include_legitimate: bool = True

class DatasetMetadata(BaseModel):
    dataset_id: str
    rows: int
    fraud_rows: int
    schema_version: str = "1.0"
    attack_ids: list[str]
    seed: int
    generator_version: str
    provenance: str
    created_at: datetime