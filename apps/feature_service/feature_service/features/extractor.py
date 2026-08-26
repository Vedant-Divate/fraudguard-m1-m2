from datetime import timedelta

from apps.feature_service.features.schema import FEATURE_NAMES, empty_feature_vector
from apps.feature_service.graph.scorer import RelationshipGraph
from shared.schemas.transaction import Transaction


def behavioral_features(
    transaction: Transaction,
    history: list[Transaction],
    window_minutes: int = 60,
) -> dict[str, float | int | bool]:
    prior_customer = [
        tx
        for tx in history
        if tx.customer_id == transaction.customer_id and tx.timestamp < transaction.timestamp
    ]
    window_start = transaction.timestamp - timedelta(minutes=window_minutes)
    recent_count = sum(1 for tx in prior_customer if window_start <= tx.timestamp < transaction.timestamp)

    prior_amounts = [tx.amount for tx in prior_customer]
    amount_mean = sum(prior_amounts) / len(prior_amounts) if prior_amounts else 0.0
    amount_deviation_ratio = (
        (transaction.amount - amount_mean) / amount_mean
        if amount_mean > 0
        else 0.0
    )

    prior_devices = {tx.device_id for tx in prior_customer if tx.device_id}
    prior_merchants = {tx.merchant_id for tx in prior_customer}
    prior_locations = [tx.location for tx in prior_customer if tx.location is not None]
    last_location = prior_locations[-1] if prior_locations else None
    location_shift = bool(
        last_location
        and transaction.location
        and (
            last_location.country != transaction.location.country
            or last_location.city != transaction.location.city
        )
    )

    return {
        "customer_txn_count_60m": recent_count,
        "customer_amount_mean_prior": round(amount_mean, 6),
        "amount_deviation_ratio": round(amount_deviation_ratio, 6),
        "is_new_device": bool(transaction.device_id and transaction.device_id not in prior_devices),
        "is_new_merchant": transaction.merchant_id not in prior_merchants,
        "location_shift": location_shift,
    }


def extract_feature_vector(
    transaction: Transaction,
    history: list[Transaction],
) -> dict[str, float | int | bool]:
    vector = empty_feature_vector()
    vector.update(behavioral_features(transaction, history))
    vector.update(RelationshipGraph.from_transactions(history).score(transaction))
    return {name: vector[name] for name in FEATURE_NAMES}


def extract_batch(transactions: list[Transaction]) -> list[dict[str, object]]:
    history: list[Transaction] = []
    rows: list[dict[str, object]] = []

    for transaction in sorted(transactions, key=lambda tx: tx.timestamp):
        vector = extract_feature_vector(transaction, history)
        rows.append(
            {
                "transaction_id": transaction.transaction_id,
                "customer_id": transaction.customer_id,
                **vector,
            }
        )
        history.append(transaction)

    return rows

