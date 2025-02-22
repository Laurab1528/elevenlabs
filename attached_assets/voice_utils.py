import requests
import json

class ElevenLabsManager:
    def __init__(self):
        self.api_key = "sk_4e43d5d8c5d56fd0b971988e24359a36bc9fe04ea98b45c4"
        self.agent_id = "l0TW76oV0MVRU4OD5svT"
        self.base_url = "https://api.elevenlabs.io/v1"

    def generate_call(self, phone_number: str, message: str) -> bool:
        try:
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "agent_id": self.agent_id,
                "phone_number": phone_number,
                "text": message
            }

            response = requests.post(
                f"{self.base_url}/text-to-speech",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            print(f"Error generating call: {str(e)}")
            return False

    def process_voice_input(self, audio_data):
        # Implement voice processing logic here
        pass

voice_manager = ElevenLabsManager()
