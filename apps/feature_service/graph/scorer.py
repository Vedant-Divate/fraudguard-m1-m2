from dataclasses import dataclass, field

from shared.schemas.transaction import Transaction


@dataclass
class RelationshipGraph:
    customer_devices: dict[str, set[str]] = field(default_factory=dict)
    customer_merchants: dict[str, set[str]] = field(default_factory=dict)
    device_customers: dict[str, set[str]] = field(default_factory=dict)
    merchant_customers: dict[str, set[str]] = field(default_factory=dict)

    @classmethod
    def from_transactions(cls, transactions: list[Transaction]) -> "RelationshipGraph":
        graph = cls()
        for tx in sorted(transactions, key=lambda item: item.timestamp):
            graph.add(tx)
        return graph

    def add(self, transaction: Transaction) -> None:
        customer = transaction.customer_id
        merchant = transaction.merchant_id
        device = transaction.device_id

        self.customer_merchants.setdefault(customer, set()).add(merchant)
        self.merchant_customers.setdefault(merchant, set()).add(customer)

        if device:
            self.customer_devices.setdefault(customer, set()).add(device)
            self.device_customers.setdefault(device, set()).add(customer)
        else:
            self.customer_devices.setdefault(customer, set())

    def score(self, transaction: Transaction) -> dict[str, float | int]:
        projected = RelationshipGraph(
            customer_devices={key: set(value) for key, value in self.customer_devices.items()},
            customer_merchants={key: set(value) for key, value in self.customer_merchants.items()},
            device_customers={key: set(value) for key, value in self.device_customers.items()},
            merchant_customers={key: set(value) for key, value in self.merchant_customers.items()},
        )
        projected.add(transaction)

        customer = transaction.customer_id
        merchant = transaction.merchant_id
        device = transaction.device_id

        customer_device_degree = len(projected.customer_devices.get(customer, set()))
        customer_merchant_degree = len(projected.customer_merchants.get(customer, set()))
        device_customer_degree = len(projected.device_customers.get(device, set())) if device else 0
        merchant_customer_degree = len(projected.merchant_customers.get(merchant, set()))
        shared_device_customer_count = max(device_customer_degree - 1, 0)

        risk = min(
            1.0,
            (shared_device_customer_count * 0.35)
            + (max(customer_device_degree - 2, 0) * 0.15)
            + (max(merchant_customer_degree - 3, 0) * 0.08),
        )

        return {
            "customer_device_degree": customer_device_degree,
            "customer_merchant_degree": customer_merchant_degree,
            "device_customer_degree": device_customer_degree,
            "merchant_customer_degree": merchant_customer_degree,
            "shared_device_customer_count": shared_device_customer_count,
            "relationship_risk_score": round(risk, 6),
        }

