import json
import traceback
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect
from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from conversational_call.twilio_audio_interface import TwilioAudioInterface
from twilio.rest import Client
import base64
import asyncio
import websockets
import sys  # Asegúrate de importar sys para manejar argumentos
import openai  # Importar la biblioteca de OpenAI
from datetime import datetime
import logging
from database import db_manager  # Importar usando la ruta absoluta
# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv('PORT', 5050))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Asegúrate de tener la API key de OpenAI

# Initialize FastAPI app
app = FastAPI()

# Initialize ElevenLabs client
eleven_labs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
ELEVEN_LABS_AGENT_ID = os.getenv("AGENT_ID")

# Inicializar el cliente de Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

@app.get("/")
async def get():
    """Render the transcription interface"""
    return HTMLResponse("""
    <html>
        <head>
            <title>Call Transcription</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                #transcription-container { max-width: 800px; margin: 0 auto; }
                #messages { 
                    height: 400px; 
                    overflow-y: auto; 
                    border: 1px solid #ccc; 
                    padding: 10px; 
                    margin-bottom: 10px;
                    background-color: #f9f9f9;
                }
                .agent-message { color: #2c5282; }
                .user-message { color: #2d3748; }
                .timestamp { color: #718096; font-size: 0.8em; }
            </style>
        </head>
        <body>
            <div id="transcription-container">
                <h1>Call Transcription</h1>
                <div id="messages"></div>
            </div>
            <script>
                const ws = new WebSocket(`ws://${window.location.host}/media-stream-eleven`);
                const messagesDiv = document.getElementById('messages');

                function addMessage(text, isAgent) {
                    const messageElement = document.createElement('p');
                    const timestamp = new Date().toLocaleTimeString();
                    messageElement.className = isAgent ? 'agent-message' : 'user-message';
                    messageElement.innerHTML = `
                        <span class="timestamp">[${timestamp}]</span> 
                        <strong>${isAgent ? 'Agent' : 'User'}:</strong> ${text}
                    `;
                    messagesDiv.appendChild(messageElement);
                    messagesDiv.scrollTop = messagesDiv.scrollHeight;
                }

                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'transcript') {
                        addMessage(data.text, data.isAgent);
                    }
                };

                ws.onerror = function(error) {
                    console.error('WebSocket Error:', error);
                };

                ws.onclose = function() {
                    addMessage('Call ended', true);
                };
            </script>
        </body>
    </html>
    """)

@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Obtener el ID del candidato desde los argumentos
    candidate_id = sys.argv[1]  # Tomar el ID del candidato del argumento

    # Inicializar la conversación con el agente
    conversation = Conversation(
        client=eleven_labs_client,
        agent_id=ELEVEN_LABS_AGENT_ID,
        audio_interface=DefaultAudioInterface(),
        callback_agent_response=lambda text: print(f"Agent said: {text}"),
        callback_user_transcript=lambda text: print(f"User said: {text}"),
    )
    
    # Lista para almacenar la transcripción
    messages = []

    try:
        # Iniciar la sesión
        conversation.start_session()
        
        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Procesar el mensaje con el agente
            response = await conversation.process_message(message['text'])
            
            # Generar audio para la respuesta
            audio = await eleven_labs_client.generate_audio(
                text=response,
                voice=ELEVEN_LABS_AGENT_ID
            )
            
            # Enviar respuesta al cliente
            await websocket.send_json({
                "text": response,
                "audio": base64.b64encode(audio).decode('utf-8')
            })

            # Agregar los mensajes a la lista
            messages.append({"user": message['text'], "agent": response})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Terminar la sesión
        conversation.end_session()

        # Generar un resumen de la conversación
        summary = await generate_summary(messages)

        # Guardar el resumen en la base de datos usando el ID del candidato
        db_manager.update_candidate(candidate_id, {
            "resumen": summary  # Guarda el resumen como comentario
        })

async def generate_summary(messages: list) -> str:
    """
    Genera un resumen inteligente de la conversación usando OpenAI.
    
    Args:
        messages (list): Lista de mensajes de la conversación.
    
    Returns:
        str: Resumen conciso de la conversación.
    """
    try:
        # Crear el prompt para el resumen
        conversation_text = "\n".join([
            f"Usuario: {msg['user']}\nAgente: {msg['agent']}\n"
            for msg in messages
        ])

        prompt = f"""
        Genera un resumen conciso y estructurado de la siguiente conversación:
        {conversation_text}
        
        El resumen debe incluir:
        1. Puntos principales discutidos
        2. Acuerdos o decisiones alcanzadas
        3. Próximos pasos o acciones a tomar (si los hay)
        4. Estado emocional general del beneficiario
        """

        # Llamar a la API de OpenAI para generar el resumen
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # O el modelo que prefieras
            messages=[{"role": "user", "content": prompt}],
            api_key=OPENAI_API_KEY
        )

        # Obtener el contenido del resumen
        summary = response['choices'][0]['message']['content']
        
        # Formatear el resumen final
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_summary = f"""
        Resumen de la llamada ({timestamp}):
        --------------------------------
        {summary}
        """

        return formatted_summary.strip()

    except Exception as e:
        logger.error(f"Error generando el resumen: {str(e)}")
        # En caso de error, devolver un resumen básico
        return f"""
        Resumen básico de la llamada ({datetime.now().strftime("%Y-%m-%d %H:%M:%S")}):
        --------------------------------
        No se pudo generar un resumen detallado. 
        La conversación consistió en {len(messages)} intercambios entre el usuario y el agente.
        """

@app.api_route("/twilio/inbound_call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response."""
    response = VoiceResponse()
    host = request.url.hostname
    connect = Connect()
    connect.stream(url=f"wss://{host}/media-stream-eleven")
    response.append(connect)
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/media-stream-eleven")
async def handle_media_stream(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established")

    audio_interface = TwilioAudioInterface(websocket)
    conversation = None

    try:
        conversation = Conversation(
            client=eleven_labs_client,
            agent_id=ELEVEN_LABS_AGENT_ID,
            audio_interface=audio_interface,
            callback_agent_response=lambda text: websocket.send_json({
                "type": "transcript",
                "text": text,
                "isAgent": True
            }),
            callback_user_transcript=lambda text: websocket.send_json({
                "type": "transcript",
                "text": text,
                "isAgent": False
            })
        )

        conversation.start_session()
        print("Conversation session started")

        async for message in websocket.iter_text():
            if not message:
                continue

            try:
                data = json.loads(message)
                await audio_interface.handle_twilio_message(data)
            except Exception as e:
                print(f"Error processing message: {str(e)}")
                traceback.print_exc()

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        if conversation:
            print("Ending conversation session...")
            conversation.end_session()
            conversation.wait_for_session_end()

@app.post("/status-callback")
async def status_callback(request: Request):
    """Handle call status callbacks"""
    form_data = await request.form()
    call_status = form_data.get('CallStatus')
    call_sid = form_data.get('CallSid')
    
    print(f"Call Status Update - SID: {call_sid}, Status: {call_status}")
    return {"status": "received"}

# Realizar la llamada
try:
    call = client.calls.create(
        to=os.getenv("TWILIO_NUMBER_TO_CALL"),
        from_=os.getenv("TWILIO_FROM_NUMBER"),
        url="https://e7af-138-84-41-184.ngrok-free.app/incoming-call",
        status_callback="https://e7af-138-84-41-184.ngrok-free.app/status-callback",
        status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
    )
    print(f"Llamada iniciada con SID: {call.sid}")
except Exception as e:
    print(f"Error al crear la llamada: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
