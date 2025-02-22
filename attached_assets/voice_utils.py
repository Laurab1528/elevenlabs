import requests
import json
import streamlit as st
import time

class ElevenLabsManager:
    def __init__(self):
        self.api_key = None
        self.base_url = "https://api.elevenlabs.io/v1"
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID

    def configure_api_key(self, api_key: str):
        """Configure the API key"""
        self.api_key = api_key

    def generate_speech(self, text: str) -> bytes:
        """Generate speech from text"""
        if not self.api_key:
            raise Exception("API key not configured")

        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Error generating speech: {response.text}")

    def generate_call(self, phone_number: str, message: str) -> bool:
        """Generate voice call with notification"""
        try:
            # For demo, we'll just show the message that would be called
            st.success(f"Voice call would be made to {phone_number} with message: {message}")
            return True
        except Exception as e:
            st.error(f"Error generating call: {str(e)}")
            return False

    def start_voice_interaction(self):
        """Start voice interaction interface"""
        st.write("Voice Interaction Demo")

        # Example voice commands
        commands = [
            "Check wallet balance",
            "Show eligible candidates",
            "Make transfer to candidate",
            "Show transaction history"
        ]

        selected_command = st.selectbox("Available Voice Commands:", commands)

        if st.button("Speak Command"):
            with st.spinner("Processing voice command..."):
                # Simulate processing delay
                time.sleep(1)

                response_text = self.process_command(selected_command)
                st.success(f"Command recognized: {selected_command}")
                st.info(f"Response: {response_text}")

                # Generate voice response
                try:
                    if self.api_key:
                        st.audio(self.generate_speech(response_text))
                    else:
                        st.warning("Please configure ElevenLabs API key for voice response")
                except Exception as e:
                    st.error(f"Error generating voice response: {str(e)}")

    def process_command(self, command: str) -> str:
        """Process voice commands and return response"""
        responses = {
            "Check wallet balance": "Your current wallet balance is 5.0 ETH",
            "Show eligible candidates": "There are 2 eligible candidates for subsidy",
            "Make transfer to candidate": "Please select a candidate for transfer",
            "Show transaction history": "You have made 3 transfers in the last month"
        }
        return responses.get(command, "Command not recognized")

voice_manager = ElevenLabsManager()