from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timezone
from shared.schemas.envelope import EnvelopeResponse, EnvelopeRequest, ErrorDetail, StatusEnum
from shared.schemas.attack import AttackScenario, MutationRequest, MutationResponse
from apps.threat_service.database import engine, Base, get_db
from apps.threat_service.models import AttackScenarioDB
from dotenv import load_dotenv
load_dotenv() # This loads the OPENAI_API_KEY from the .env file

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
    from apps.threat_service.llm.discover_agent import discover_chain
    
    # For MVP, we cycle through categories the LLM can target
    target_category = payload.data.get("category", "ACCOUNT_TAKEOVER")
    
    # Run the LangGraph agent
    result = discover_chain.invoke({"category": target_category})
    
    if result.get("error"):
        return EnvelopeResponse(
            request_id=payload.request_id,
            timestamp=datetime.now(timezone.utc),
            data={"status": "failed", "error": result["error"], "candidate": None}
        )
        
    candidate = result.get("validated_scenario")
    
    # In a full system, you would insert this into the DB here.
    # For now, we just return the candidate for the user to review.
    return EnvelopeResponse(
        request_id=payload.request_id,
        timestamp=datetime.now(timezone.utc),
        data={"status": "success", "candidate": candidate}
    )

@app.get("/api/v1/attacks")
async def list_attacks(db: Session = Depends(get_db)):
    attacks = db.query(AttackScenarioDB).all()
    # Convert SQLAlchemy objects to Pydantic schemas
    attacks_data = [AttackScenario.model_validate(a) for a in attacks]
    return EnvelopeResponse(
        request_id=generate_request_id(),
        timestamp=datetime.now(timezone.utc),
        data={"count": len(attacks_data), "attacks": attacks_data}
    )


@app.get("/api/v1/attacks/{attack_id}")
async def get_attack(attack_id: str, db: Session = Depends(get_db)):
    attack = db.query(AttackScenarioDB).filter(AttackScenarioDB.attack_id == attack_id).first()
    if not attack:
        raise HTTPException(status_code=404, detail="Attack not found")
    # Convert SQLAlchemy object to Pydantic schema
    attack_data = AttackScenario.model_validate(attack)
    return EnvelopeResponse(
        request_id=generate_request_id(),
        timestamp=datetime.now(timezone.utc),
        data=attack_data
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