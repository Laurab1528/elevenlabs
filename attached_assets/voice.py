import os
import tempfile
import speech_recognition as sr
from gtts import gTTS
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
import streamlit as st

def voice_interface():
    """Función para la interfaz de voz"""
    load_dotenv("./conversational_call/.env")
    agent_id = os.getenv("ELEVENLABS_AGENT_ID")
    api_key = os.getenv("ELEVENLABS_API_KEY")

    client = ElevenLabs(api_key=api_key)
    conversation = Conversation(
        client,
        agent_id,
        requires_auth=bool(api_key),
        audio_interface=DefaultAudioInterface(),
        callback_agent_response=lambda response: print(f"Agente: {response}"),
        callback_user_transcript=lambda transcript: print(f"Usuario: {transcript}")
    )

    st.title("Interfaz de Voz")

    if st.button("Iniciar Reconocimiento de Voz"):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.write("Por favor, hable ahora...")
            audio = recognizer.listen(source)

            try:
                text = recognizer.recognize_google(audio, language='es-ES')
                st.write(f"Usted dijo: {text}")

                # Iniciar la conversación con ElevenLabs
                conversation.start_session()
                conversation_id = conversation.wait_for_session_end()
                st.write(f"ID de Conversación: {conversation_id}")

                # Respuesta del agente
                response = f"Usted dijo: {text}. ¿Cómo puedo ayudarle?"
                st.write(response)

                # Convertir la respuesta a voz
                tts = gTTS(response, lang='es')
                with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                    tts.save(f"{tmp_file.name}.mp3")
                    st.audio(f"{tmp_file.name}.mp3", format="audio/mp3")

            except sr.UnknownValueError:
                st.error("No se pudo entender el audio.")
            except sr.RequestError as e:
                st.error(f"No se pudo solicitar resultados; {e}")



