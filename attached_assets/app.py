# import streamlit as st
#from lovable import Lovable as st  # Asegúrate de que la biblioteca Lovable esté instalada
from datetime import datetime
import pandas as pd
from database import db_manager, init_db
import os
from dotenv import load_dotenv  # Asegúrate de instalar python-dotenv si no lo tienes
from openai import OpenAI
from voice import voice_interface # Asegúrate de importar la función
import streamlit as st


# Cargar las variables de entorno desde el archivo .env
load_dotenv("./conversational_call/.env")

# Inicializar el cliente de OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Inicializar la base de datos
db = init_db()

def init_session_state():
    """Inicializa las variables de estado de la sesión"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"
    if 'phone_number' not in st.session_state:
        st.session_state.phone_number = None

def simple_phone_transfer(from_phone: str, to_phone: str, amount: float) -> tuple[bool, str]:
    """
    Función simple para simular una transferencia usando números de teléfono
    """
    try:
        # Aquí puedes implementar la lógica real de transferencia
        print(f"Transferring ${amount} from {from_phone} to {to_phone}")
        return True, "Transfer successful!"
    except Exception as e:
        return False, f"Transfer failed: {str(e)}"

def phone_configuration():
    """Configuración del número de teléfono para transferencias"""
    st.subheader("Phone Configuration")

    if not st.session_state.phone_number:
        st.warning("Please configure your phone number to perform transactions")

        with st.form("phone_config"):
            phone_number = st.text_input(
                "Phone Number",
                help="Your phone number in international format (e.g., +1234567890)"
            )

            if st.form_submit_button("Save Phone Configuration"):
                # Validación básica del número de teléfono
                if phone_number and phone_number.startswith('+'):
                    st.session_state.phone_number = phone_number
                    st.success("Phone number configured successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a valid phone number starting with '+'")
    else:
        st.success("Phone is configured")
        st.info(f"Current phone number: {st.session_state.phone_number}")
        if st.button("Reset Phone Configuration"):
            st.session_state.phone_number = None
            st.rerun()

async def get_best_candidate(prompt):
    """Función asíncrona para obtener el mejor candidato usando OpenAI"""
    messages = [
        {"role": "developer", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": prompt
        }
    ]
    completion = await client.chat.completions.create(
        model="gpt-4o",  # Asegúrate de que este modelo esté disponible
        messages=messages
    )
    return completion.choices[0].message.content

def candidate_management():
    """Gestión de candidatos y transferencias"""
    if not st.session_state.phone_number:
        st.error("Please configure your phone number first")
        phone_configuration()
        return

    st.subheader("Candidate Management")

    # List candidates
    st.subheader("Eligible Candidates")
    candidates = db.get_all_candidates()
    
    if candidates:
        # Convertir la lista de candidatos a un DataFrame
        df = pd.DataFrame([{
            'Name': c.name,
            'ID': c.identification,
            'Phone': c.phone,
            'Last Subsidy': c.last_subsidy.strftime('%Y-%m-%d') if c.last_subsidy else 'Never',
            'Is Eligible': c.is_eligible
        } for c in candidates])

        st.dataframe(df)

        # Crear un prompt para el modelo de OpenAI
        candidate_info = "\n".join([f"Name: {c.name}, ID: {c.identification}, Last Subsidy: {c.last_subsidy}, Is Eligible: {c.is_eligible}" for c in candidates])
        
        # Llamar al modelo de OpenAI para seleccionar el mejor candidato
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "developer", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": f"De los siguientes candidatos, ¿quién es el mejor candidato para recibir un subsidio?\n{candidate_info}. proporcionar solo [nombre, identificacion, subsidio]"
                }
            ]
        )

        best_candidate_info = completion.choices[0].message.content
        st.subheader("Mejor Candidato Seleccionado")
        st.write(best_candidate_info)

        # Extraer el nombre del mejor candidato del resultado de manera más segura
        try:
            parts = best_candidate_info.split(":")
            if len(parts) > 1:
                best_candidate_name = parts[1].strip()
                # Buscar el candidato en la base de datos usando db_manager
                selected_candidate = db_manager.get_candidate_by_name(best_candidate_name)  # Asegúrate de que esta función exista
            else:
                raise ValueError("El formato de la respuesta no es el esperado.")
        except (IndexError, AttributeError, ValueError) as e:
            # Lógica alternativa: seleccionar el candidato con subsidio None o el más antiguo
            best_candidate_name = None
            best_candidate = None  # Definir best_candidate antes de usarlo
            for candidate in candidates:
                if candidate.last_subsidy is None:
                    best_candidate_name = candidate.name
                    best_candidate = candidate
                    break
                elif best_candidate_name is None or (candidate.last_subsidy and candidate.last_subsidy < best_candidate.last_subsidy):
                    best_candidate_name = candidate.name
                    best_candidate = candidate

        # Buscar el candidato en la base de datos
        selected_candidate = next((c for c in candidates if c.name == best_candidate_name), None)

        if selected_candidate:
            # Mostrar toda la información del candidato seleccionado
            st.subheader("Información del Candidato Seleccionado")
            st.write(f"Nombre: {selected_candidate.name}")
            st.write(f"ID: {selected_candidate.identification}")
            st.write(f"Teléfono: {selected_candidate.phone}")
            st.write(f"Elegible: {'Sí' if selected_candidate.is_eligible else 'No'}")
            
            # Verificar si existe el atributo notes
            notes = getattr(selected_candidate, 'notes', 'No hay notas disponibles')
            st.write(f"Notas: {notes}")

            amount = st.number_input("Amount ($)", min_value=1.0, value=10.0, step=1.0)

            if st.button("Transfer Subsidy"):
                success, message = simple_phone_transfer(
                    st.session_state.phone_number,
                    selected_candidate.phone,
                    amount
                )

                if success:
                    db.update_candidate(selected_candidate.identification, {
                        "last_subsidy": datetime.now()
                    })

                    call_message = f"Hello {selected_candidate.name}, you have received a subsidy of ${amount}."
                    os.system(f"python conversational_call/main.py {selected_candidate.phone} {call_message}")

                    st.success("Transfer successful and notification call initiated!")
                else:
                    st.error(f"Transfer error: {message}")
        else:
            st.error("No candidate found.")
    else:
        st.error("No candidates in the system")

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

def main():
    """Función principal de la aplicación"""
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
            ["Configuración de Teléfono", "Gestión de Candidatos", "Interfaz de Voz"]
        )

        if menu == "Configuración de Teléfono":
            phone_configuration()
        elif menu == "Gestión de Candidatos":
            candidate_management()
        elif menu == "Interfaz de Voz":
            voice_interface()  # Llama a la función de voice.py

        if st.sidebar.button("Cerrar sesión"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.phone_number = None
            st.rerun()

if __name__ == "__main__":
    main()