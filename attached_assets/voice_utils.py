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

        # User input section
        user_message = st.text_input("Type your message (or speak if your browser supports it):",
                                   key="user_message")

        if st.button("Send Message"):
            if user_message:
                with st.spinner("AI is processing..."):
                    try:
                        # Make API call to ElevenLabs for AI response
                        url = f"{self.base_url}/talk-to/chat"
                        headers = {
                            "xi-api-key": self.api_key,
                            "Content-Type": "application/json"
                        }

                        payload = {
                            "agent_id": self.agent_id,
                            "message": user_message
                        }

                        response = requests.post(url, headers=headers, json=payload)

                        if response.status_code == 200:
                            response_data = response.json()
                            # Display AI's text response
                            st.write("AI:", response_data.get('text', 'No response text'))

                            # Play audio response
                            if 'audio' in response_data:
                                st.audio(response_data['audio'], format='audio/mp3')
                        else:
                            st.error(f"Error communicating with AI: {response.text}")
                    except Exception as e:
                        st.error(f"Error during voice interaction: {str(e)}")
            else:
                st.warning("Please enter a message first")

        # Display instructions
        with st.expander("How to use the voice chat"):
            st.markdown("""
            1. Type your message in the text box or use your browser's speech-to-text feature
            2. Click 'Send Message' to interact with the AI
            3. The AI will respond with both text and voice
            4. Continue the conversation naturally

            Note: This is connected to the ElevenLabs Talk-To AI agent for natural conversation.
            """)

voice_manager = ElevenLabsManager()