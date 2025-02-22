import streamlit as st
from datetime import datetime
import pandas as pd
from database import db_manager, init_db, Candidate
from ethereum_manager import eth_manager
from voice_utils import voice_manager

# Initialize the database
init_db()

def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"
    if 'wallet_configured' not in st.session_state:
        st.session_state.wallet_configured = False
    if 'wallet_address' not in st.session_state:
        st.session_state.wallet_address = None
    if 'private_key' not in st.session_state:
        st.session_state.private_key = None

def wallet_configuration():
    st.subheader("Wallet Configuration")

    if not st.session_state.wallet_configured:
        st.warning("Please configure your Ethereum wallet to perform transactions")

        # For demo purposes, we'll use example values
        example_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
        example_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

        with st.form("wallet_config"):
            wallet_address = st.text_input("Ethereum Wallet Address", 
                                         value=example_address,
                                         help="Your Ethereum wallet address")
            private_key = st.text_input("Private Key", 
                                      value=example_key,
                                      type="password",
                                      help="Your wallet's private key (Keep this secret!)")

            if st.form_submit_button("Save Wallet Configuration"):
                st.session_state.wallet_address = wallet_address
                st.session_state.private_key = private_key
                st.session_state.wallet_configured = True
                eth_manager.configure_wallet(wallet_address, private_key)
                st.success("Wallet configured successfully!")
                st.rerun()
    else:
        st.success("Wallet is configured")
        st.info(f"Current wallet address: {st.session_state.wallet_address[:6]}...{st.session_state.wallet_address[-4:]}")
        if st.button("Reset Wallet Configuration"):
            st.session_state.wallet_configured = False
            st.session_state.wallet_address = None
            st.session_state.private_key = None
            st.rerun()

def login_page():
    st.title("Sistema de Gestión de Subsidios")
    st.header("Iniciar Sesión")

    username = st.text_input("Usuario", key="login_username")
    password = st.text_input("Contraseña", type="password", key="login_password")

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Iniciar Sesión", use_container_width=True):
            success, message = db_manager.authenticate_user(username, password)
            if success:
                st.session_state.authenticated = True
                st.session_state.current_user = username
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with col2:
        if st.button("Registrarse", use_container_width=True):
            st.session_state.current_page = "register"
            st.rerun()

    if st.button("¿Olvidaste tu contraseña?", type="secondary"):
        st.session_state.current_page = "recover"
        st.rerun()

def register_page():
    st.title("Sistema de Gestión de Subsidios")
    st.header("Registro de Usuario")

    with st.form("registration"):
        new_username = st.text_input("Usuario")
        new_email = st.text_input("Email")
        new_password = st.text_input("Contraseña", type="password")
        confirm_password = st.text_input("Confirmar Contraseña", type="password")

        col1, col2 = st.columns([1, 1])

        with col1:
            submit = st.form_submit_button("Registrar", use_container_width=True)

        with col2:
            if st.form_submit_button("Volver al Login", use_container_width=True):
                st.session_state.current_page = "login"
                st.rerun()

        if submit:
            if new_password != confirm_password:
                st.error("Las contraseñas no coinciden")
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
            elif db_manager.reset_password(recovery_email, reset_code, new_pass):
                st.success("Password updated successfully")
                st.session_state.current_page = "login"
                st.rerun()
            else:
                st.error("Invalid or expired code")

def candidate_management():
    if not st.session_state.wallet_configured:
        st.error("Please configure your wallet first")
        wallet_configuration()
        return

    st.subheader("Candidate Management")

    # Add new candidate
    with st.expander("Add New Candidate"):
        with st.form("new_candidate"):
            name = st.text_input("Name")
            identification = st.text_input("ID")
            address = st.text_input("Address")
            phone = st.text_input("Phone")
            wallet = st.text_input("Ethereum Address")

            if st.form_submit_button("Add Candidate"):
                candidate_data = {
                    "name": name,
                    "identification": identification,
                    "address": address,
                    "phone": phone,
                    "wallet_address": wallet
                }
                if db_manager.add_candidate(candidate_data):
                    st.success("Candidate added successfully!")
                else:
                    st.error("Error adding candidate")

    # List candidates
    st.subheader("Candidate List")
    candidates = db_manager.get_all_candidates()
    if candidates:
        df = pd.DataFrame([{
            'Name': c.name,
            'ID': c.identification,
            'Phone': c.phone,
            'Eligible': c.is_eligible,
            'Last Subsidy': c.last_subsidy.strftime('%Y-%m-%d') if c.last_subsidy else 'Never'
        } for c in candidates])

        st.dataframe(df)

        # Subsidy Transfer
        st.subheader("Transfer Subsidy")
        selected_id = st.selectbox("Select Candidate", [c.identification for c in candidates])
        amount = st.number_input("Amount (ETH)", min_value=0.0, value=0.1)

        if st.button("Transfer Subsidy"):
            candidate = db_manager.get_candidate(selected_id)
            if candidate and candidate.is_eligible:
                success, message = eth_manager.transfer_eth(
                    st.session_state.wallet_address,
                    candidate.wallet_address,
                    amount
                )

                if success:
                    # Update candidate's last subsidy date
                    candidate_data = {
                        "last_subsidy": datetime.now()
                    }
                    db_manager.update_candidate(selected_id, candidate_data)

                    # Generate automated call
                    call_message = f"Hello {candidate.name}, you have received a subsidy of {amount} ETH."
                    voice_manager.generate_call(candidate.phone, call_message)

                    st.success("Transfer successful and notification call initiated!")
                else:
                    st.error(f"Transfer error: {message}")
            else:
                st.error("Candidate is not eligible for subsidy yet")

def voice_interface():
    st.subheader("Voice Interface")

    if st.button("Start Voice Interaction"):
        # Here you would implement the voice interaction logic
        st.info("Voice interaction feature in development")

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
        st.title("Sistema de Gestión de Subsidios")

        menu = st.sidebar.selectbox(
            "Navegación",
            ["Configuración de la Billetera", "Gestión de Candidatos", "Interfaz de Voz"]
        )

        if menu == "Configuración de la Billetera":
            wallet_configuration()
        elif menu == "Gestión de Candidatos":
            candidate_management()
        elif menu == "Interfaz de Voz":
            voice_interface()

        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.wallet_configured = False
            st.session_state.wallet_address = None
            st.session_state.private_key = None
            st.rerun()

if __name__ == "__main__":
    main()