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

    def add_user(self, username: str, password: str, email: str) -> bool:
        if username in self.users:
            return False
        self.users[username] = User(username=username, password=password, email=email)
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

    def add_candidate(self, candidate_data: dict) -> bool:
        try:
            candidate = Candidate(**candidate_data)
            self.candidates[candidate.identification] = candidate
            return True
        except Exception as e:
            print(f"Error adding candidate: {str(e)}")
            return False

    def get_candidate(self, identification: str) -> Optional[Candidate]:
        return self.candidates.get(identification)

    def get_all_candidates(self) -> List[Candidate]:
        return list(self.candidates.values())

    def update_candidate(self, identification: str, candidate_data: dict):
        if identification in self.candidates:
            current_candidate = self.candidates[identification]
            for key, value in candidate_data.items():
                setattr(current_candidate, key, value)

    def delete_candidate(self, identification: str):
        if identification in self.candidates:
            del self.candidates[identification]

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

# Create a singleton instance of the database
db_manager = InMemoryDB()

def init_db():
    """Initialize the database with any required setup"""
    # For in-memory database, we just ensure the manager exists
    return db_manager