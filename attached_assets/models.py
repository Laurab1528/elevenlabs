from datetime import datetime, timedelta
from pydantic import BaseModel, validator, EmailStr
from typing import Optional

class User(BaseModel):
    username: str
    password: str
    email: EmailStr
    recovery_code: Optional[str] = None
    recovery_code_expiry: Optional[datetime] = None

class Candidate(BaseModel):
    name: str
    identification: str
    address: str
    phone: str
    last_subsidy: Optional[datetime]
    wallet_address: str
    
    @property
    def is_eligible(self):
        if not self.last_subsidy:
            return True
        return datetime.now() - self.last_subsidy > timedelta(days=60)

class Transaction(BaseModel):
    from_address: str
    to_address: str
    amount: float
    timestamp: datetime