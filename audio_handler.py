import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AudioProcessor:
    def __init__(self):
        # Obtenemos la key y limpiamos comillas accidentales de Render o del .env
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            api_key = api_key.strip().strip('"').strip("'")
            
        self.client = OpenAI(api_key=api_key)

    def transcribe_audio_file(self, file_path: str) -> str:
        """
        Toma la ruta de un archivo de audio local (.mp3, .wav, .m4a, .oga)
        y lo transcribe usando el modelo Whisper de OpenAI.
        """
        if not os.path.exists(file_path):
            print(f"No se encontró el archivo de audio en: {file_path}")
            return ""
            
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