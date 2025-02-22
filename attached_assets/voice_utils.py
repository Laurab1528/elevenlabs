import requests
import json
import streamlit as st
import time

class ElevenLabsManager:
    def __init__(self):
        self.api_key = "sk_81fc48f4c6b08d28bcc13e648f4de6ec4bc7c4b4ef7c1ac5"
        self.agent_id = "l0TW76oV0MVRU4OD5svT"
        self.base_url = "https://api.elevenlabs.io/v1"

    def generate_call(self, phone_number: str, message: str) -> bool:
        """Generate voice call with notification using ElevenLabs Talk API"""
        try:
            url = f"{self.base_url}/talk-to/call"
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "agent_id": self.agent_id,
                "phone_number": phone_number,
                "text": message
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                st.success("Voice call initiated successfully!")
                return True
            else:
                st.error(f"Error initiating call: {response.text}")
                return False
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

        if st.button("Execute Command"):
            with st.spinner("Processing command..."):
                response_text = self.process_command(selected_command)
                st.success(f"Command executed: {selected_command}")
                st.info(f"Response: {response_text}")

                # Make API call to ElevenLabs for voice response
                try:
                    url = f"{self.base_url}/talk-to/respond"
                    headers = {
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json"
                    }

                    payload = {
                        "agent_id": self.agent_id,
                        "text": response_text
                    }

                    response = requests.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        audio_data = response.content
                        st.audio(audio_data, format='audio/mp3')
                    else:
                        st.warning("Could not generate voice response")
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