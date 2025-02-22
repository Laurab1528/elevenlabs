import requests
import json
import streamlit as st
import time

class ElevenLabsManager:
    def __init__(self):
        self.api_key = "sk_81fc48f4c6b08d28bcc13e648f4de6ec4bc7c4b4ef7c1ac5"
        self.agent_id = "l0TW76oV0MVRU4OD5svT"
        self.base_url = "https://api.elevenlabs.io/v1"

    def start_voice_interaction(self):
        """Create an interactive voice chat interface"""
        st.write("## Voice Chat with AI Assistant")
        st.markdown("Click 'Execute Model' to start talking with the AI assistant.")

        if st.button("Execute Model", use_container_width=True):
            with st.spinner("AI Assistant is ready..."):
                try:
                    # Make API call to ElevenLabs for AI response
                    url = f"{self.base_url}/talk-to/chat"
                    headers = {
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json"
                    }

                    payload = {
                        "agent_id": self.agent_id,
                        "mode": "conversation"
                    }

                    response = requests.post(url, headers=headers, json=payload)

                    if response.status_code == 200:
                        response_data = response.json()
                        st.success("AI Assistant is active! You can start speaking.")

                        # Display conversation area
                        st.markdown("""
                        ### Conversation
                        The AI assistant is listening. Speak naturally and the assistant will respond with voice.
                        """)

                        # Show status
                        status = st.empty()
                        status.info("Listening...")
                    else:
                        st.error(f"Error initiating conversation: {response.text}")
                except Exception as e:
                    st.error(f"Error during voice interaction: {str(e)}")

        # Display instructions
        with st.expander("How to use the voice chat"):
            st.markdown("""
            1. Click 'Execute Model' to start the conversation
            2. Once active, speak naturally to the AI assistant
            3. The AI will respond with voice automatically
            4. Continue the conversation naturally

            Note: Make sure your browser has permission to use your microphone.
            """)

voice_manager = ElevenLabsManager()