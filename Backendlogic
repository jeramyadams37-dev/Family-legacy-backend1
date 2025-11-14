from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import random

from models import SessionLocal, Family, Member, Fund, Transaction, ChatMessage
import schemas

app = FastAPI()

# Allow React to talk to Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, set to your Netlify/Vercel URL or specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ROUTES ---

@app.post("/families", response_model=schemas.FamilyOut)
def create_family(family: schemas.FamilyCreate, db: Session = Depends(get_db)):
    # 1. Create Family
    new_family = Family(name=family.family_name)
    db.add(new_family)
    db.commit()
    db.refresh(new_family)

    # 2. Create Initial Members
    for m in family.initial_members:
        new_member = Member(family_id=new_family.id, name=m.name, role=m.role)
        db.add(new_member)
    
    # 3. Initialize Fund
    new_fund = Fund(family_id=new_family.id, balance=0, staked_balance=0, total_earned=0)
    db.add(new_fund)
    db.commit()

    return {
        "id": new_family.id,
        "family_name": new_family.name,
        "member_count": len(family.initial_members)
    }

@app.get("/families/{family_id}", response_model=schemas.FamilyOut)
def get_family(family_id: int, db: Session = Depends(get_db)):
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    return {
        "id": family.id,
        "family_name": family.name,
        "member_count": len(family.members)
    }

@app.get("/families/{family_id}/members", response_model=List[schemas.MemberOut])
def get_members(family_id: int, db: Session = Depends(get_db)):
    return db.query(Member).filter(Member.family_id == family_id).all()

@app.get("/families/{family_id}/fund", response_model=schemas.FundOut)
def get_fund(family_id: int, db: Session = Depends(get_db)):
    fund = db.query(Fund).filter(Fund.family_id == family_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    # Format transactions for React
    txns = []
    for t in fund.transactions[-10:]: # Get last 10
        txns.append({
            "type": t.type,
            "description": t.description,
            "amount_dollars": t.amount
        })
        
    return {
        "balance_dollars": fund.balance,
        "staked_balance_dollars": fund.staked_balance,
        "total_earned_dollars": fund.total_earned,
        "recent_transactions": txns
    }

@app.post("/chat")
def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    # 1. Save User Message
    user_msg = ChatMessage(family_id=request.family_id, role="user", content=request.message)
    db.add(user_msg)
    
    # 2. GENERATE AI RESPONSE
    # In a real app, call OpenAI/Anthropic API here.
    # For now, we simulate a response.
    ai_response_text = f"That's interesting! Tell me more about how your family feels about {request.message}."
    
    # 3. Save Assistant Message
    ai_msg = ChatMessage(family_id=request.family_id, role="assistant", content=ai_response_text)
    db.add(ai_msg)
    db.commit()
    
    return {"response": ai_response_text}

@app.post("/data/submit")
def submit_data(payload: schemas.DataSubmit, db: Session = Depends(get_db)):
    # This endpoint is called by the frontend after a chat to "monetize" the interaction
    
    if payload.allow_marketplace:
        # 1. Calculate Reward (Simulated)
        reward = 0.05 # 5 cents per interaction
        
        # 2. Update Fund
        fund = db.query(Fund).filter(Fund.family_id == payload.family_id).first()
        if fund:
            fund.balance += reward
            fund.total_earned += reward
            
            # 3. Create Transaction Record
            txn = Transaction(
                fund_id=fund.id,
                amount=reward,
                type="data_reward",
                description="Chat interaction reward"
            )
            db.add(txn)
            db.commit()
            
            return {"status": "success", "reward": reward}
            
    return {"status": "success", "reward": 0}

@app.post("/insights/generate")
def generate_insights(request: schemas.InsightRequest, db: Session = Depends(get_db)):
    # 1. Fetch recent chat history
    chats = db.query(ChatMessage).filter(ChatMessage.family_id == request.family_id).all()
    
    # 2. Analyze (Simulated AI Analysis)
    # Real app: Send chat logs to LLM to summarize
    
    return {
        "insights": {
            "communication_style": "Your family uses very positive language.",
            "primary_topics": "School, Vacations, and Dinner plans.",
            "sentiment_trend": "Increasingly happy over the last week."
        }
    }
