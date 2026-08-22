from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone
from shared.schemas.envelope import EnvelopeResponse, EnvelopeRequest, ErrorDetail, StatusEnum
from shared.schemas.attack import AttackScenario, MutationRequest, MutationResponse
from apps.threat_service.database import engine, Base, get_db
from apps.threat_service.models import AttackScenarioDB

app = FastAPI(title="FraudGuard 360 - Threat Intelligence", docs_url="/docs")

# Create tables on startup
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

def generate_request_id() -> str:
    return f"REQ_{uuid4().hex[:12]}"

@app.get("/health")
async def health():
    return EnvelopeResponse(
        request_id=generate_request_id(),
        timestamp=datetime.now(timezone.utc),
        data={"status": "healthy"}
    )

@app.post("/api/v1/attacks/discover")
async def discover_attacks(payload: EnvelopeRequest):
    # TODO: Trigger LangGraph Agent here
    return EnvelopeResponse(
        request_id=payload.request_id,
        timestamp=datetime.now(timezone.utc),
        data={"message": "LLM discovery initiated. Await approval."}
    )

@app.get("/api/v1/attacks")
async def list_attacks(db: Session = Depends(get_db)):
    attacks = db.query(AttackScenarioDB).all()
    return EnvelopeResponse(
        request_id=generate_request_id(),
        timestamp=datetime.now(timezone.utc),
        data={"count": len(attacks), "attacks": attacks}
    )

@app.get("/api/v1/attacks/{attack_id}")
async def get_attack(attack_id: str, db: Session = Depends(get_db)):
    attack = db.query(AttackScenarioDB).filter(AttackScenarioDB.attack_id == attack_id).first()
    if not attack:
        raise HTTPException(status_code=404, detail="Attack not found")
    return EnvelopeResponse(
        request_id=generate_request_id(),
        timestamp=datetime.now(timezone.utc),
        data=attack
    )

@app.post("/api/v1/attacks/mutate")
async def mutate_attack(payload: EnvelopeRequest):
    req_data = MutationRequest(**payload.data)
    # TODO: Apply mutation operators and save to DB
    return EnvelopeResponse(
        request_id=payload.request_id,
        timestamp=datetime.now(timezone.utc),
        data=MutationResponse(
            new_attack_id=f"{req_data.attack_id}_V2",
            version="1.1",
            parent_provenance={"source": "mutation", "parent_attack_id": req_data.attack_id}
        )
    )