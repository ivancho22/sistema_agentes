import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AudioProcessor:
    def __init__(self):
        # Inicializa el cliente oficial de OpenAI usando la API Key del .env
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def transcribe_audio_file(self, file_path: str) -> str:
        """
        Toma la ruta de un archivo de audio local (.mp3, .wav, .m4a, .oga)
        y lo transcribe usando el modelo Whisper de OpenAI.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No se encontró el archivo de audio en: {file_path}")
            
        try:
            with open(file_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    language="es" # Forzamos que interprete el español perfectamente
                )
            return transcription.text
        except Exception as e:
            print(f"Error al transcribir con OpenAI Whisper: {e}")
            return ""