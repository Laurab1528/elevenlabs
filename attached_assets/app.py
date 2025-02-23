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
from typing import Dict, List
import random  # Asegúrate de importar la biblioteca random

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
        Analyzes all candidates and returns the one that needs the subsidy the most.

        Returns:
            Candidate: The selected candidate.
        """
        candidates = db_manager.get_all_candidates()  # Get all candidates
        if not candidates:
            raise ValueError("The database must contain at least one candidate (ID001, ID002, ID003)")

        # Sort candidates by last_subsidy (ascending), prioritizing the oldest subsidy
        candidates.sort(key=lambda c: c.last_subsidy if c.last_subsidy else datetime.min)

        # Prepare candidate information for the model
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

        # Create a message for the model
        analysis_prompt = SystemMessage(content=f"""
        Analyze the following list of candidates and select the one that needs the subsidy the most:
        {candidates_info}
        
        IMPORTANT: Your response must be ONLY the ID of the selected candidate, for example: 'ID001'
        """)

        # Send the message to the model and get the response
        response = await self.model.ainvoke([analysis_prompt])
        
        # Get the candidate ID and clean it from any additional text
        selected_candidate_id = response.content.strip()

        print(selected_candidate_id)
        
        # Verify that the ID exists before returning it
        selected_candidate = db_manager.get_candidate(selected_candidate_id)

        # If the model did not select a valid candidate, take the first one (oldest last_subsidy)
        if selected_candidate is None:
            logger.warning("The model did not select a valid candidate. Selecting the candidate with the oldest last_subsidy instead.")
            selected_candidate = candidates[0]  # Take the first candidate in the sorted list

        return selected_candidate

    def extract_candidate_id(self, analysis_result: str) -> str:
        """
        Extrae el ID del candidato del resultado del análisis.
        
        Args:
            analysis_result (str): Resultado del análisis.
            
        Returns:
            str: ID del candidato.
        """
        # Como el modelo está configurado para devolver solo el ID,
        # simplemente limpiamos cualquier espacio en blanco
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
    st.subheader("Candidate Management")

    # Obtener todos los candidatos
    candidates = db_manager.get_all_candidates()
    
    if not candidates:
        st.error("No candidates available.")
        return

    # Análisis de candidatos para seleccionar el mejor
    agent = CandidateAnalysisAgent()
    selected_candidate = asyncio.run(agent.analyze_candidates())

    # Mostrar la información del candidato seleccionado
    st.info(f"Selected candidate: {selected_candidate.name} (ID: {selected_candidate.identification})")
    
    # Mostrar información adicional del candidato
    st.write(f"Address: {selected_candidate.address}")
    st.write(f"Phone: {selected_candidate.phone}")
    st.write(f"Last subsidy: {selected_candidate.last_subsidy.strftime('%Y-%m-%d') if selected_candidate.last_subsidy else 'Never'}")

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

def start_conversation(candidate: Candidate):
    # Aquí se llamaría al main de la conversación, pasando el ID del candidato
    os.system(f"python attached_assets/conversational_call/main.py {candidate.identification}")

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
