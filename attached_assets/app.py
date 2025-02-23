import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import os
import random
from pydantic import BaseModel
import streamlit as st  # Asumimos que esta es una aplicación Streamlit
import database

# Configuración de logging
logging.basicConfig(level=logging.INFO)

class Candidate:
    def __init__(self, name, identification, address, phone, last_subsidy):
        self.name = name
        self.identification = identification
        self.address = address
        self.phone = phone
        self.last_subsidy = last_subsidy

# Simulación de db_manager para obtener candidatos
class db_manager:
    @staticmethod
    def get_all_candidates():
        # Llamar a la lógica de la base de datos para obtener candidatos
        return database.db_manager.get_all_candidates()  # Asegúrate de que este método exista en database.py
    
    @staticmethod
    def update_candidate(candidate_id: str, data: Dict):
        # Aquí se actualizarían los datos del candidato en la base de datos.
        print(f"Updating candidate {candidate_id} with data: {data}")
    
# Funciones simuladas
def transfer_via_phone(phone: str, amount: float) -> Tuple[bool, str]:
    """Simula la transferencia de dinero por teléfono."""
    # Siempre retorna éxito
    return True, "Transfer successful"

def start_conversation(candidate: Candidate):
    """Inicia una conversación con el candidato."""
    # Aquí iría la lógica de la conversación
    print(f"Starting conversation with candidate: {candidate.name} (ID: {candidate.identification})")


# Simplificado, ahora solo con una estructura de flujo
class AgentOrchestrator:
    """
    Orquestador que maneja el flujo de la aplicación utilizando listas y diccionarios.
    """
    def __init__(self):
        self.state = []
        
    def add_step(self, step_name: str, data: Dict) -> None:
        """Agrega un paso al flujo."""
        step = {"step_name": step_name, "data": data}
        self.state.append(step)
        
    def execute_flow(self, selected_candidate: Candidate):
        """
        Ejecuta el flujo principal de la aplicación y maneja el estado.
        """
        try:
            # 1. Flujo de selección de candidato
            self.add_step("candidate_selection", {"status": "started", "candidate_id": selected_candidate.identification})
            self.add_step("candidate_selected", {"candidate_id": selected_candidate.identification})

            # 2. Flujo de transferencia
            self.add_step("transfer", {"status": "started"})
            
            # Lógica de transferencia
            amount = st.number_input("Amount to transfer (USD)", min_value=10, value=10, step=5)
            success, message = transfer_via_phone(selected_candidate.phone, amount)
            
            if success:
                self.add_step("transfer_successful", {"candidate_id": selected_candidate.identification, "amount": amount})
                
                # 3. Flujo de llamada
                self.add_step("call", {"status": "started"})
                start_conversation(selected_candidate)
                self.add_step("call_initiated", {"candidate_id": selected_candidate.identification})
            else:
                self.add_step("transfer_failed", {"candidate_id": selected_candidate.identification, "message": message})
            
            return True
            
        except Exception as e:
            self.add_step("error", {"error": str(e)})
            return False

    def save_state(self) -> Dict:
        """Guarda el estado actual del flujo"""
        return {"state": self.state}
        
    def load_state(self, state: Dict) -> None:
        """Carga un estado previo"""
        self.state = state.get("state", [])

def candidate_management():
    st.subheader("Candidate Management")

    # Obtener todos los candidatos desde db_manager
    candidates = db_manager.get_all_candidates()

    if not candidates:
        st.error("No candidates available.")
        return

    orchestrator = AgentOrchestrator()

    # Selección del candidato (supongamos que seleccionamos el primero de la lista)
    selected_candidate = candidates[0]  # Puedes implementar la lógica para seleccionar al mejor candidato

    # Mostrar la información del candidato seleccionado
    st.info(f"Selected candidate: {selected_candidate.name} (ID: {selected_candidate.identification})")

    # Proceso de transferencia
    amount = st.number_input("Amount to transfer (USD)", min_value=10, value=10, step=5)

    if st.button("Confirm Transfer"):
        success, message = transfer_via_phone(selected_candidate.phone, amount)

        if success:
            # Actualizar solo last_subsidy
            db_manager.update_candidate(selected_candidate.identification, {
                "last_subsidy": datetime.now()
            })

            st.success("Transfer successful!")
            os.system(f"python conversational_call/main.py {selected_candidate.identification}")
        else:
            st.error(f"Error in transfer: {message}")

    # Ejecutar el flujo de orquestación con el candidato seleccionado
    orchestrator.execute_flow(selected_candidate)

def main():

    
    candidate_management()

if __name__ == "__main__":
    main()

