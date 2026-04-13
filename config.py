import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

SAMPLE_RATE = 24000
SILENCE_DURATION = 300
WS_URL = "wss://api.openai.com/v1/realtime"

SESSION_CONFIG = {
    "type": "transcription",
    "audio": {
        "input": {
            "format": {
                "type": "audio/pcm",
                "rate": SAMPLE_RATE,
            },
            # "noise_reduction": None,
            "noise_reduction": {
                "type": "near_field",
            },
            "transcription": {
                "language": "de",
                "model": "whisper-1",
                "prompt": (
                    "Bitte transkribiere die folgende Algorithmen und Wahrscheinlichkeiten Vorlesung wortgetreu und "
                    "in vollständigen Sätzen. Achte darauf, Fachbegriffe korrekt "
                    "zu schreiben und Formeln oder Symbole so klar wie möglich "
                    "wiederzugeben."
                ),
            },
            "turn_detection": {
                "type": "server_vad",
                "threshold": 0.8,
                "prefix_padding_ms": 300,
                "silence_duration_ms": SILENCE_DURATION,
            },
        },
    },
}