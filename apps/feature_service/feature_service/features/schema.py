from typing import Literal

from pydantic import BaseModel


FEATURE_SCHEMA_VERSION = "1.0"


class FeatureField(BaseModel):
    name: str
    dtype: Literal["float", "int", "bool"]
    description: str


FEATURE_FIELDS: tuple[FeatureField, ...] = (
    FeatureField(
        name="customer_txn_count_60m",
        dtype="int",
        description="Prior transactions by the same customer in the trailing 60 minutes.",
    ),
    FeatureField(
        name="customer_amount_mean_prior",
        dtype="float",
        description="Mean amount of prior transactions for the same customer.",
    ),
    FeatureField(
        name="amount_deviation_ratio",
        dtype="float",
        description="Current amount minus prior customer mean, divided by prior mean.",
    ),
    FeatureField(
        name="is_new_device",
        dtype="bool",
        description="True when the device has not been seen before for this customer.",
    ),
    FeatureField(
        name="is_new_merchant",
        dtype="bool",
        description="True when the merchant has not been seen before for this customer.",
    ),
    FeatureField(
        name="location_shift",
        dtype="bool",
        description="True when country or city differs from the most recent known customer location.",
    ),
    FeatureField(
        name="customer_device_degree",
        dtype="int",
        description="Number of distinct devices linked to this customer after including the transaction.",
    ),
    FeatureField(
        name="customer_merchant_degree",
        dtype="int",
        description="Number of distinct merchants linked to this customer after including the transaction.",
    ),
    FeatureField(
        name="device_customer_degree",
        dtype="int",
        description="Number of distinct customers linked to this device after including the transaction.",
    ),
    FeatureField(
        name="merchant_customer_degree",
        dtype="int",
        description="Number of distinct customers linked to this merchant after including the transaction.",
    ),
    FeatureField(
        name="shared_device_customer_count",
        dtype="int",
        description="Other customers that have used this transaction's device.",
    ),
    FeatureField(
        name="relationship_risk_score",
        dtype="float",
        description="Normalized graph relationship risk from shared device and density signals.",
    ),
)

FEATURE_NAMES: tuple[str, ...] = tuple(field.name for field in FEATURE_FIELDS)


def empty_feature_vector() -> dict[str, float | int | bool]:
    return {field.name: False if field.dtype == "bool" else 0 for field in FEATURE_FIELDS}

