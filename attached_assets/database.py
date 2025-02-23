from datetime import datetime, timedelta
import secrets
from typing import Dict, List, Optional, Tuple
from models import User, Candidate, Transaction

class InMemoryDB:
    def __init__(self):
        self.users: Dict[str, User] = {}
        # Inicializar con candidatos de ejemplo
        self.candidates: Dict[str, Candidate] = {
            "ID001": Candidate(
                name="John Smith",
                identification="ID001",
                address="123 Main St",
                phone="+1234567890",
                wallet_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                last_subsidy=None,
                resumen="Familia de 4 miembros, desempleado desde hace 6 meses",
             
            ),
            "ID002": Candidate(
                name="Alice Johnson",
                identification="ID002",
                address="456 Oak Ave",
                phone="+1987654321",
                wallet_address="0x941C3C374f856C6e86c44F929491338B",
                last_subsidy=datetime.now() - timedelta(days=70),
                resumen="Madre soltera, dos hijos en edad escolar",
                
            ),
            "ID003": Candidate(
                name="Bob Wilson",
                identification="ID003",
                address="789 Pine Rd",
                phone="+1122334455",
                wallet_address="0xA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6",
                last_subsidy=datetime.now() - timedelta(days=30),
                resumen="Desempleado, busca trabajo activamente",
                
            )
        }
        self.transactions: List[Transaction] = []

    # Keep existing user management methods
    def add_user(self, username: str, password: str, email: str) -> Tuple[bool, str]:
        if username in self.users:
            return False, "Username already exists"

        for user in self.users.values():
            if user.email == email:
                return False, "Email is already registered"

        if len(password) < 6:
            return False, "Password must be at least 6 characters long"

        try:
            new_user = User(username=username, password=password, email=email)
            self.users[username] = new_user
            return True, "User registered successfully"
        except Exception as e:
            return False, f"Error registering user: {str(e)}"

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        if username not in self.users:
            return False, "User not found"

        user = self.users[username]
        if user.password != password:
            return False, "Incorrect password"

        return True, "Authentication successful"

    def generate_recovery_code(self, email: str) -> Optional[str]:
        for user in self.users.values():
            if user.email == email:
                recovery_code = secrets.token_hex(3)
                user.recovery_code = recovery_code
                user.recovery_code_expiry = datetime.now() + timedelta(minutes=30)
                return recovery_code
        return None

    def reset_password(self, email: str, recovery_code: str, new_password: str) -> Tuple[bool, str]:
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

    # Simplified candidate management (read-only)
    def get_candidate(self, identification: str) -> Optional[Candidate]:
        return self.candidates.get(identification)

    def get_all_candidates(self) -> List[Candidate]:
        return list(self.candidates.values())

    def update_candidate(self, identification: str, candidate_data: dict):
        """
        Actualiza la información de un candidato.
        
        Args:
            identification (str): ID del candidato a actualizar
            candidate_data (dict): Diccionario con los datos a actualizar
        """
        if identification in self.candidates:
            current_candidate = self.candidates[identification]
            # Crear un nuevo diccionario con los datos actuales
            updated_data = current_candidate.dict()
            # Actualizar con los nuevos datos
            updated_data.update(candidate_data)
            # Crear un nuevo objeto Candidate con los datos actualizados
            self.candidates[identification] = Candidate(**updated_data)

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

# Crear una instancia singleton de la base de datos
db_manager = InMemoryDB()

def init_db():
    """Inicializa la base de datos con la configuración requerida"""
    return db_manager