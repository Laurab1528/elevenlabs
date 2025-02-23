from datetime import datetime, timedelta
from pydantic import BaseModel, validator
from typing import Optional

class User(BaseModel):
    username: str
    password: str
    email: str
    recovery_code: Optional[str] = None
    recovery_code_expiry: Optional[datetime] = None

class Candidate(BaseModel):
    name: str
    identification: str
    address: str
    phone: str
    last_subsidy: Optional[datetime]
    wallet_address: str
    resumen: Optional[str] = None  # Resumen de la situación del candidato
    
    
    @property
    def is_eligible(self):
        if not self.last_subsidy:
            return True
        return datetime.now() - self.last_subsidy > timedelta(days=60)

    def update_resumen(self, new_resumen: str):
        """
        Actualiza el resumen del candidato con la información de la llamada.
        
        Args:
            new_resumen (str): El nuevo resumen que se desea establecer.
        """
        self.resumen = new_resumen

    def update_comments(self, new_comments: str):
        """
        Actualiza los comentarios del candidato.
        
        Args:
            new_comments (str): Los nuevos comentarios que se desean establecer.
        """
        self.comments = new_comments

class Transaction(BaseModel):
    from_address: str
    to_address: str
    amount: float
    timestamp: datetime