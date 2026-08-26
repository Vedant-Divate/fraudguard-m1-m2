import json
import os
from pathlib import Path

import pandas as pd

from apps.feature_service.features.extractor import extract_batch
from shared.schemas.transaction import Location, Transaction


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _configured_roots(extra_roots: list[str] | None = None) -> list[Path]:
    roots = [PROJECT_ROOT]

    env_roots = os.getenv("FEATURE_DATA_ROOTS", "")
    for raw_root in env_roots.split(os.pathsep):
        if raw_root.strip():
            roots.append(Path(raw_root.strip()).expanduser())

    for raw_root in extra_roots or []:
        if raw_root.strip():
            roots.append(Path(raw_root.strip()).expanduser())

    for ancestor in PROJECT_ROOT.parents:
        sibling_fraudguard = ancestor / "FraudGuard"
        if sibling_fraudguard.exists():
            roots.append(sibling_fraudguard)

    unique_roots: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_roots.append(resolved)
    return unique_roots


def _dataset_candidates(dataset_id: str, extra_roots: list[str] | None = None) -> list[Path]:
    dataset_path = Path(dataset_id).expanduser()
    candidates = []
    if dataset_path.exists():
        candidates.append(dataset_path.resolve())

    for root in _configured_roots(extra_roots):
        candidates.extend(
            [
                root / "data" / "synthetic" / dataset_id,
                root / "data" / "fixtures" / dataset_id,
                root / dataset_id,
            ]
        )
    return candidates


def _load_manifest(dataset_dir: Path) -> dict[str, object]:
    manifest_path = dataset_dir / "manifest.json"
    if not manifest_path.exists():
        return {}
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _transaction_from_row(row: dict[str, object]) -> Transaction:
    row = {
        key: None if pd.isna(value) else value
        for key, value in dict(row).items()
    }
    country = row.pop("country", None)
    city = row.pop("city", None)
    if "location" not in row and country and city:
        row["location"] = Location(country=str(country), city=str(city))
    return Transaction(**row)


def load_dataset(dataset_id: str, source_roots: list[str] | None = None) -> tuple[list[Transaction], dict[str, object], Path]:
    for dataset_dir in _dataset_candidates(dataset_id, source_roots):
        parquet_path = dataset_dir / "transactions.parquet"
        csv_path = dataset_dir / "transactions.csv"
        if parquet_path.exists():
            frame = pd.read_parquet(parquet_path)
            return (
                [_transaction_from_row(row) for row in frame.to_dict(orient="records")],
                _load_manifest(dataset_dir),
                dataset_dir,
            )
        if csv_path.exists():
            frame = pd.read_csv(csv_path)
            return (
                [_transaction_from_row(row) for row in frame.to_dict(orient="records")],
                _load_manifest(dataset_dir),
                dataset_dir,
            )
    raise FileNotFoundError(
        f"Dataset {dataset_id} was not found in configured roots, data/synthetic, or data/fixtures."
    )


def load_transactions(dataset_id: str, source_roots: list[str] | None = None) -> list[Transaction]:
    transactions, _, _ = load_dataset(dataset_id, source_roots)
    return transactions


def _with_training_metadata(
    feature_rows: list[dict[str, object]],
    transactions: list[Transaction],
    manifest: dict[str, object],
) -> list[dict[str, object]]:
    transaction_by_id = {tx.transaction_id: tx for tx in transactions}
    source_schema_version = str(manifest.get("schema_version", "1.0"))
    generator_version = manifest.get("generator_version")
    dataset_provenance = manifest.get("provenance")

    rows = []
    for row in feature_rows:
        tx = transaction_by_id[str(row["transaction_id"])]
        rows.append(
            {
                **row,
                "is_fraud": tx.is_fraud,
                "attack_id": tx.attack_id,
                "source_schema_version": source_schema_version,
                "generator_version": generator_version,
                "dataset_provenance": dataset_provenance,
            }
        )
    return rows


def write_feature_dataset(dataset_id: str, source_roots: list[str] | None = None) -> dict[str, object]:
    transactions, manifest, source_dir = load_dataset(dataset_id, source_roots)
    rows = extract_batch(transactions)
    rows = _with_training_metadata(rows, transactions, manifest)
    output_dir = PROJECT_ROOT / "data" / "features" / dataset_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "features.parquet"
    pd.DataFrame(rows).to_parquet(output_path, index=False)
    return {
        "dataset_id": dataset_id,
        "rows": len(rows),
        "fraud_rows": sum(1 for tx in transactions if tx.is_fraud),
        "attack_ids": sorted({tx.attack_id for tx in transactions if tx.attack_id}),
        "source_dataset_path": str(source_dir),
        "output_path": str(output_path.relative_to(PROJECT_ROOT)),
    }
