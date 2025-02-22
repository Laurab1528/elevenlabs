from datetime import datetime, timedelta
import secrets
from typing import Dict, List, Optional, Tuple
from models import User, Candidate, Transaction

class InMemoryDB:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.candidates: Dict[str, Candidate] = {}
        self.transactions: List[Transaction] = []

    def add_user(self, username: str, password: str, email: str) -> Tuple[bool, str]:
        """
        Register a new user with validations
        Returns (success, message)
        """
        # Validate username doesn't exist
        if username in self.users:
            return False, "Username already exists"

        # Validate email isn't in use
        for user in self.users.values():
            if user.email == email:
                return False, "Email is already registered"

        # Validate password length
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"

        # Create and save new user
        try:
            new_user = User(username=username, password=password, email=email)
            self.users[username] = new_user
            return True, "User registered successfully"
        except Exception as e:
            return False, f"Error registering user: {str(e)}"

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate a user
        Returns (success, message)
        """
        if username not in self.users:
            return False, "User not found"

        user = self.users[username]
        if user.password != password:
            return False, "Incorrect password"

        return True, "Authentication successful"

    def generate_recovery_code(self, email: str) -> Optional[str]:
        """Generate recovery code for an email"""
        for user in self.users.values():
            if user.email == email:
                recovery_code = secrets.token_hex(3)
                user.recovery_code = recovery_code
                user.recovery_code_expiry = datetime.now() + timedelta(minutes=30)
                return recovery_code
        return None

    def reset_password(self, email: str, recovery_code: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset password using a recovery code
        Returns (success, message)
        """
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long"

        for user in self.users.values():
            if (user.email == email and 
                user.recovery_code == recovery_code and 
                user.recovery_code_expiry and 
                user.recovery_code_expiry > datetime.now()):
                user.password = new_password
                user.recovery_code = None
                user.recovery_code_expiry = None
                return True, "Password updated successfully"
        return False, "Invalid or expired recovery code"

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
    """Initialize the database with required configuration"""
    return db_manager