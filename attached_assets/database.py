from datetime import datetime, timedelta
import secrets
from typing import Dict, List, Optional, Tuple
from models import User, Candidate, Transaction

class InMemoryDB:
    def __init__(self):
        self.users: Dict[str, User] = {
            "admin": User(username="admin", password="admin123", email="admin@example.com")
        }
        self.candidates: Dict[str, Candidate] = {}
        self.transactions: List[Transaction] = []

    def add_user(self, user: User) -> bool:
        if user.username in self.users:
            return False
        self.users[user.username] = user
        return True

    def authenticate_user(self, username: str, password: str) -> bool:
        if username in self.users and self.users[username].password == password:
            return True
        return False

    def generate_recovery_code(self, email: str) -> Optional[str]:
        for user in self.users.values():
            if user.email == email:
                recovery_code = secrets.token_hex(3)
                user.recovery_code = recovery_code
                user.recovery_code_expiry = datetime.now() + timedelta(minutes=30)
                return recovery_code
        return None

    def reset_password(self, email: str, recovery_code: str, new_password: str) -> bool:
        for user in self.users.values():
            if (user.email == email and 
                user.recovery_code == recovery_code and 
                user.recovery_code_expiry and 
                user.recovery_code_expiry > datetime.now()):
                user.password = new_password
                user.recovery_code = None
                user.recovery_code_expiry = None
                return True
        return False

    def add_candidate(self, candidate: Candidate):
        self.candidates[candidate.identification] = candidate

    def get_candidate(self, identification: str) -> Candidate:
        return self.candidates.get(identification)

    def get_all_candidates(self) -> List[Candidate]:
        return list(self.candidates.values())

    def update_candidate(self, identification: str, candidate: Candidate):
        self.candidates[identification] = candidate

    def delete_candidate(self, identification: str):
        if identification in self.candidates:
            del self.candidates[identification]

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

db = InMemoryDB()