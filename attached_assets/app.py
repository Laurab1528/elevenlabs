import streamlit as st
from datetime import datetime
import pandas as pd
from database import db_manager, init_db
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import openai
from models import Candidate
import asyncio
from dotenv import load_dotenv
import logging
from typing import Dict, List, Optional
import random  # Asegúrate de importar la biblioteca random
from pydantic import BaseModel

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(__file__), 'conversational_call/.env'))

# Initialize the database
init_db()

# Now you can access the environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("🚨 The OpenAI API key is not configured. Please set the 'OPENAI_API_KEY' environment variable.")

# Configurar OpenAI API
openai.api_key = OPENAI_API_KEY

# Definición del modelo de candidato usando Pydantic
class Candidate(BaseModel):
    name: str
    identification: str
    address: str
    phone: str
    last_subsidy: Optional[datetime] = None
    resumen: Optional[str] = None

# Definición de dependencias para el agente
class CandidateDependencies:
    db: any  # Aquí puedes especificar el tipo de tu conexión a la base de datos

# Definición del agente de análisis de candidatos
class CandidateAnalysisAgent:
    """
    Clase que representa un agente de análisis de candidatos.
    """

    def __init__(self):
        """
        Inicializa el agente con la API key de OpenAI.
        """
        self.model = self.initialize_openai_client()

    def initialize_openai_client(self) -> ChatOpenAI:
        """
        Inicializa el cliente de OpenAI.

        Returns:
            ChatOpenAI: Modelo de OpenAI inicializado.
        """
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=OPENAI_API_KEY
        )

    async def analyze_candidates(self) -> Candidate:
        """
        Analiza todos los candidatos y devuelve el que más necesita el subsidio.

        Returns:
            Candidate: El candidato seleccionado.
        """
        candidates = db_manager.get_all_candidates()  # Obtener todos los candidatos
        if not candidates:
            raise ValueError("La base de datos debe contener al menos un candidato (ID001, ID002, ID003)")

        # Ordenar candidatos por last_subsidy (ascendente)
        candidates.sort(key=lambda c: c.last_subsidy if c.last_subsidy else datetime.min)

        # Preparar información de los candidatos para el modelo
        candidates_info = "\n".join([
            f"Candidate: {c.name}\n"
            f"ID: {c.identification}\n"
            f"Last subsidy: {c.last_subsidy.strftime('%Y-%m-%d') if c.last_subsidy else 'Never'}\n"
            f"Address: {c.address}\n"
            f"Phone: {c.phone}\n"
            f"Summary: {c.resumen if hasattr(c, 'resumen') else 'No summary'}\n"
            "---"
            for c in candidates
        ])

        # Crear un mensaje para el modelo
        analysis_prompt = SystemMessage(content=f"""
        Analyze the following list of candidates and select the one that needs the subsidy the most:
        {candidates_info}
        
        IMPORTANT: Your response must be ONLY the ID of the selected candidate, for example: 'ID001'
        """)

        # Enviar el mensaje al modelo y obtener la respuesta
        response = await self.model.ainvoke([analysis_prompt])
        
        # Obtener el ID del candidato seleccionado
        selected_candidate_id = response.content.strip()
        
        # Verificar que el ID exista antes de devolverlo
        selected_candidate = db_manager.get_candidate(selected_candidate_id)

        # Si el modelo no seleccionó un candidato válido, tomar el primero (más antiguo)
        if selected_candidate is None:
            logger.warning("El modelo no seleccionó un candidato válido. Seleccionando el candidato con el subsidio más antiguo.")
            selected_candidate = candidates[0]  # Tomar el primer candidato en la lista ordenada

        return selected_candidate

    def extract_candidate_id(self, analysis_result: str) -> str:
        """
        Extrae el ID del candidato del resultado del análisis.
        
        Args:
            analysis_result (str): Resultado del análisis.
            
        Returns:
            str: ID del candidato.
        """
        return analysis_result.strip()

    def get_candidates(self) -> List[Candidate]:
        """
        Obtiene todos los candidatos de la base de datos.

        Returns:
            List[Candidate]: Lista de candidatos disponibles.
        """
        candidates = db_manager.get_all_candidates()  # Obtener todos los candidatos
        if not candidates:
            return []
            
        return candidates


class StateType(Dict):
    """Tipo de estado para el grafo"""
    candidates: List[Candidate]
    analysis_result: str
    recommendation: Dict
    transfer_details: Dict
    user_confirmed: bool
    transfer_confirmed: bool
    call_summary: str

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"
    if 'wallet_configured' not in st.session_state:
        st.session_state.wallet_configured = False
    if 'agent' not in st.session_state:
        st.session_state.agent = CandidateAnalysisAgent()  # Ya no necesitamos pasar la API key
    if 'analysis_state' not in st.session_state:
        st.session_state.analysis_state = None

def login_page():
    st.title("Subsidy Management System")
    st.header("Login")

    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Login", use_container_width=True):
            success, message = db_manager.authenticate_user(username, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.current_user = username
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with col2:
        if st.button("Sign Up", use_container_width=True):
            st.session_state.current_page = "register"
            st.rerun()

    if st.button("Forgot Password?", type="secondary"):
        st.session_state.current_page = "recover"
        st.rerun()

def register_page():
    st.title("Subsidy Management System")
    st.header("User Registration")

    with st.form("registration"):
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        col1, col2 = st.columns([1, 1])

        with col1:
            submit = st.form_submit_button("Register", use_container_width=True)

        with col2:
            if st.form_submit_button("Back to Login", use_container_width=True):
                st.session_state.current_page = "login"
                st.rerun()

        if submit:
            if new_password != confirm_password:
                st.error("Passwords don't match")
            else:
                success, message = db_manager.add_user(new_username, new_password, new_email)
                if success:
                    st.success(message)
                    st.session_state.current_page = "login"
                    st.rerun()
                else:
                    st.error(message)

def recover_page():
    st.title("Subsidy Management System")
    st.header("Password Recovery")

    recovery_email = st.text_input("Email", key="recovery_email")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("Request Code", use_container_width=True):
            recovery_code = db_manager.generate_recovery_code(recovery_email)
            if recovery_code:
                st.success(f"Recovery code: {recovery_code}")
            else:
                st.error("Email not found")

    with col2:
        if st.button("Back to Login", use_container_width=True):
            st.session_state.current_page = "login"
            st.rerun()

    st.markdown("---")

    with st.form("reset_password"):
        st.subheader("Change Password")
        reset_code = st.text_input("Recovery Code")
        new_pass = st.text_input("New Password", type="password")
        confirm_new_pass = st.text_input("Confirm New Password", type="password")

        if st.form_submit_button("Change Password", use_container_width=True):
            if new_pass != confirm_new_pass:
                st.error("Passwords don't match")
            else:
                success, message = db_manager.reset_password(recovery_email, reset_code, new_pass)
                if success:
                    st.success(message)
                    st.session_state.current_page = "login"
                    st.rerun()
                else:
                    st.error(message)

def candidate_management():
    # Get the selected candidate
    try:
        candidate = asyncio.run(st.session_state.agent.analyze_candidates())
        
        # Display candidate information
        st.write(f"Selected candidate: {candidate.name}")
        st.write(f"Phone: {candidate.phone}")
        
        # Transfer section
        amount = st.number_input("Amount to transfer (USD)", min_value=10, value=10, step=5)
        if st.button("Transfer and Start Call"):
            success, message = transfer_via_phone(candidate.phone, amount)
            if success:
                st.success(message)
                start_conversation(candidate)
            else:
                st.error(message)
                
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

def start_conversation(candidate: Candidate):
    # Aquí se llamaría al main de la conversación, pasando el ID del candidato
    os.system(f"python conversational_call/main.py {candidate.identification}")

def transfer_via_phone(phone_number, amount):
    # Logic to transfer money to the phone number using pix (Brazil), Bre-B (Colombia)
    return True, "Transfer completed successfully"

def main():
    init_session_state()

    if not st.session_state.authenticated:
        if st.session_state.current_page == "login":
            login_page()
        elif st.session_state.current_page == "register":
            register_page()
        elif st.session_state.current_page == "recover":
            recover_page()
    else:
        st.title("Subsidy Management System")

        menu = st.sidebar.selectbox(
            "Navigation",
            ["Candidate Management"]
        )

        if menu == "Candidate Management":
            candidate_management()

        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.wallet_configured = False
            st.rerun()

if __name__ == "__main__":
    main()