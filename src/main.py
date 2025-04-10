import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import aiplatform
from pydantic import BaseModel

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
PROMPT = """Sei un assistente AI esperto di interpretazione di messaggi vocali.
Ti verra' presentato un testo estratto da una nota vocale. Sara' tra i tag <nota> e </nota>. Il tuo compito e' fornire un riassunto completo della nota.
Linee guida:
- includi tutto cio' che e' importante di questa nota
- correggi la sintassi, punteggiatura ed errori grammaticali
- presenta un riassunto schematico della nota

<nota>
{text}
</nota>
"""

aiplatform.init(project=PROJECT_ID, location=LOCATION)

def transcribe_audio(audio_bytes):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        sample_rate_hertz=48000,
        language_code="it-IT",
        alternative_language_codes=["en-US"],
        enable_automatic_punctuation=True
    )

    response = client.recognize(config=config, audio=audio)
    transcript = " ".join([r.alternatives[0].transcript for r in response.results])
    return transcript.strip()

# def summarize_text(text):
#     model = aiplatform.TextGenerationModel.from_pretrained("text-bison")
#     response = model.predict(prompt=PROMPT.format(text=text), temperature=0)
#     return response.text.strip()

@app.post("/")
async def webhook(request: Request):
    data = await request.json()
    voice = data.get("message", {}).get("voice")
    if not voice:
        return PlainTextResponse("No voice message", status_code=400)

    file_id = voice["file_id"]

    file_path_resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile",
        data={"file_id": file_id}
    )
    file_path = file_path_resp.json()["result"]["file_path"]

    audio_resp = requests.get(
        f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    )
    audio_bytes = audio_resp.content

    transcript = transcribe_audio(audio_bytes)
    # summary = summarize_text(transcript)

    chat_id = data["message"]["chat"]["id"]
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        data={"chat_id": chat_id, "text": transcript}
    )

    return PlainTextResponse("OK", status_code=200)
    