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
        Registra un nuevo usuario con validaciones
        Retorna (éxito, mensaje)
        """
        # Validar que el usuario no exista
        if username in self.users:
            return False, "El nombre de usuario ya existe"

        # Validar que el email no esté en uso
        for user in self.users.values():
            if user.email == email:
                return False, "El email ya está registrado"

        # Validar longitud de contraseña
        if len(password) < 6:
            return False, "La contraseña debe tener al menos 6 caracteres"

        # Crear y guardar el nuevo usuario
        try:
            new_user = User(username=username, password=password, email=email)
            self.users[username] = new_user
            return True, "Usuario registrado exitosamente"
        except Exception as e:
            return False, f"Error al registrar usuario: {str(e)}"

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Autentica un usuario
        Retorna (éxito, mensaje)
        """
        if username not in self.users:
            return False, "Usuario no encontrado"

        user = self.users[username]
        if user.password != password:
            return False, "Contraseña incorrecta"

        return True, "Autenticación exitosa"

    def generate_recovery_code(self, email: str) -> Optional[str]:
        """Genera código de recuperación para un email"""
        for user in self.users.values():
            if user.email == email:
                recovery_code = secrets.token_hex(3)
                user.recovery_code = recovery_code
                user.recovery_code_expiry = datetime.now() + timedelta(minutes=30)
                return recovery_code
        return None

    def reset_password(self, email: str, recovery_code: str, new_password: str) -> Tuple[bool, str]:
        """
        Resetea la contraseña usando un código de recuperación
        Retorna (éxito, mensaje)
        """
        if len(new_password) < 6:
            return False, "La nueva contraseña debe tener al menos 6 caracteres"

        for user in self.users.values():
            if (user.email == email and 
                user.recovery_code == recovery_code and 
                user.recovery_code_expiry and 
                user.recovery_code_expiry > datetime.now()):
                user.password = new_password
                user.recovery_code = None
                user.recovery_code_expiry = None
                return True, "Contraseña actualizada exitosamente"
        return False, "Código de recuperación inválido o expirado"

    # Los métodos de gestión de candidatos se mantienen igual
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

# Crear una instancia singleton de la base de datos
db_manager = InMemoryDB()

def init_db():
    """Inicializa la base de datos con la configuración requerida"""
    return db_manager