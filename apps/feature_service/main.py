from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from apps.feature_service.batch import write_feature_dataset
from apps.feature_service.features.extractor import extract_feature_vector
from apps.feature_service.features.schema import FEATURE_FIELDS, FEATURE_SCHEMA_VERSION
from apps.feature_service.graph.scorer import RelationshipGraph
from apps.feature_service.store import FeatureStore
from shared.schemas.envelope import EnvelopeRequest, EnvelopeResponse, ErrorDetail, StatusEnum
from shared.schemas.transaction import Transaction


app = FastAPI(title="FraudGuard 360 - Feature Engineering", docs_url="/docs")
store = FeatureStore()


class BatchRequest(BaseModel):
    dataset_id: str
    source_roots: list[str] | None = None


def generate_request_id() -> str:
    return f"REQ_{uuid4().hex[:12]}"


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=EnvelopeResponse(
            request_id="unknown",
            timestamp=datetime.now(timezone.utc),
            status=StatusEnum.ERROR,
            error=ErrorDetail(code=code, message=message),
        ).model_dump(mode="json"),
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return error_response(422, "VALIDATION_ERROR", str(exc))


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return error_response(422, "VALIDATION_ERROR", str(exc))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return error_response(exc.status_code, "HTTP_ERROR", str(exc.detail))


@app.get("/health")
async def health() -> EnvelopeResponse[dict[str, str]]:
    return EnvelopeResponse(
        request_id=generate_request_id(),
        timestamp=datetime.now(timezone.utc),
        data={"status": "healthy"},
    )


@app.get("/api/v1/features/schema")
async def feature_schema() -> EnvelopeResponse[dict[str, object]]:
    return EnvelopeResponse(
        request_id=generate_request_id(),
        timestamp=datetime.now(timezone.utc),
        data={
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "features": [field.model_dump() for field in FEATURE_FIELDS],
        },
    )


@app.post("/api/v1/features/extract")
async def extract_features(payload: EnvelopeRequest) -> EnvelopeResponse[dict[str, object]]:
    transaction = Transaction(**(payload.data or {}))
    vector = extract_feature_vector(transaction, store.history())
    store.add(transaction)
    return EnvelopeResponse(
        request_id=payload.request_id,
        timestamp=datetime.now(timezone.utc),
        data={
            "transaction_id": transaction.transaction_id,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "features": vector,
        },
    )


@app.post("/api/v1/graph/risk")
async def graph_risk(payload: EnvelopeRequest) -> EnvelopeResponse[dict[str, object]]:
    transaction = Transaction(**(payload.data or {}))
    score = RelationshipGraph.from_transactions(store.history()).score(transaction)
    return EnvelopeResponse(
        request_id=payload.request_id,
        timestamp=datetime.now(timezone.utc),
        data={
            "transaction_id": transaction.transaction_id,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "graph": score,
        },
    )


@app.post("/api/v1/features/batch")
async def batch_features(payload: EnvelopeRequest) -> EnvelopeResponse[dict[str, object]]:
    request = BatchRequest(**(payload.data or {}))
    try:
        result = write_feature_dataset(request.dataset_id, request.source_roots)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return EnvelopeResponse(
        request_id=payload.request_id,
        timestamp=datetime.now(timezone.utc),
        data={"feature_schema_version": FEATURE_SCHEMA_VERSION, **result},
    )

