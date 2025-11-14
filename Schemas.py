from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Inputs ---
class MemberCreate(BaseModel):
    name: str
    role: str

class FamilyCreate(BaseModel):
    family_name: str
    initial_members: List[MemberCreate]

class ChatRequest(BaseModel):
    family_id: int
    member_id: int
    message: str

class DataSubmit(BaseModel):
    family_id: int
    data_type: str
    data: dict
    allow_marketplace: bool

class InsightRequest(BaseModel):
    family_id: int

# --- Outputs (Must match React props) ---
class TransactionOut(BaseModel):
    type: str
    description: str
    amount_dollars: float

class FundOut(BaseModel):
    balance_dollars: float
    staked_balance_dollars: float
    total_earned_dollars: float
    recent_transactions: List[TransactionOut]

class MemberOut(BaseModel):
    id: int
    name: str
    role: str

class FamilyOut(BaseModel):
    id: int
    family_name: str
    member_count: int
