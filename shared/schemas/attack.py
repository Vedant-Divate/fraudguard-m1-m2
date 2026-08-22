from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum
from datetime import datetime

class AttackCategory(str, Enum):
    ACCOUNT_TAKEOVER = "ACCOUNT_TAKEOVER"
    SYNTHETIC_IDENTITY = "SYNTHETIC_IDENTITY"
    CARD_NOT_PRESENT = "CARD_NOT_PRESENT"
    UPI_SCAM = "UPI_SCAM"
    MULE_NETWORK = "MULE_NETWORK"
    BOT_ACCOUNT_TESTING = "BOT_ACCOUNT_TESTING"
    REFUND_ABUSE = "REFUND_ABUSE"
    FRIENDLY_FRAUD = "FRIENDLY_FRAUD"
    TRANSACTION_LAUNDERING = "TRANSACTION_LAUNDERING"
    PROMOTION_ABUSE = "PROMOTION_ABUSE"
    KYC_SIMULATION = "KYC_SIMULATION"
    IMPERSONATION_SOCIAL_ENGINEERING = "IMPERSONATION_SOCIAL_ENGINEERING"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AttackParameters(BaseModel):
    new_device: Optional[bool] = False
    velocity_multiplier: Optional[int] = 1
    location_shift: Optional[bool] = False
    amount_anomaly_z: Optional[float] = 0.0
    time_window_minutes: Optional[int] = 60
    merchant_novelty: Optional[bool] = False

class Provenance(BaseModel):
    source: str = "manual"
    parent_attack_id: Optional[str] = None
    mutation_operators: list[str] = []

class AttackScenario(BaseModel):
    attack_id: str
    version: str = "1.0"
    category: AttackCategory
    channel: str
    risk_level: RiskLevel
    description: str
    parameters: AttackParameters
    features: list[str]
    novelty_score: float = 0.0
    provenance: Provenance = Provenance()
    simulation_ready: bool = True

class MutationRequest(BaseModel):
    attack_id: str
    operators: list[dict[str, Any]] # e.g., [{"name": "bump_velocity", "params": {"multiplier": 5}}]