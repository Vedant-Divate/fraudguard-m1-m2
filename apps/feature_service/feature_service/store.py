from collections import defaultdict
from datetime import datetime

from shared.schemas.transaction import Transaction


class FeatureStore:
    def __init__(self) -> None:
        self._transactions: list[Transaction] = []

    def add(self, transaction: Transaction) -> None:
        self._transactions.append(transaction)

    def history(self) -> list[Transaction]:
        return sorted(self._transactions, key=lambda tx: tx.timestamp)

    def prior_for_customer(self, customer_id: str, before: datetime) -> list[Transaction]:
        return [
            tx
            for tx in self._transactions
            if tx.customer_id == customer_id and tx.timestamp < before
        ]

    def grouped_by_customer(self) -> dict[str, list[Transaction]]:
        grouped: dict[str, list[Transaction]] = defaultdict(list)
        for tx in self.history():
            grouped[tx.customer_id].append(tx)
        return dict(grouped)

    def clear(self) -> None:
        self._transactions.clear()

