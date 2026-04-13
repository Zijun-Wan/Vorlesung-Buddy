# Vorlesung Buddy -- Real-Time Lecture Transcription

A low-latency real-time transcription system for lectures using
streaming audio and WebSockets.\
Built with a modular pipeline design for scalability and
experimentation.

------------------------------------------------------------------------

## Features

-   Real-time audio capture from microphone
-   Low-latency streaming transcription via WebSocket
-   Multi-threaded pipeline (capture → encode → send → receive → process)
-   Timestamp tracking and latency measurement
-   Easily configurable parameters
-   Modular and extensible architecture

------------------------------------------------------------------------

## Architecture Overview

    AudioProducer → AudioEncoder → OutboundSender → WebSocket → Receiver → TranscriptProcessor

-   **AudioProducer**: captures raw audio chunks
-   **AudioEncoder**: encodes audio to base64
-   **OutboundSender**: sends audio + control messages to the OpenAI realtime transcription websocket 
-   **Receiver**: receives events messages from the websocket
-   **TranscriptProcessor**: handles and orders transcripts

------------------------------------------------------------------------

## Installation

### 1. Clone the repository

    git clone git@github.com:Zijun-Wan/Vorlesung-Buddy.git
    cd Vorlesung-Buddy

### 2. Create a virtual environment

    python3 -m venv .venv
    source .venv/bin/activate

### 3. Install dependencies

    pip install -r requirements.txt

If `requirements.txt` is missing:

    pip install websocket-client sounddevice soundfile python-dotenv requests

------------------------------------------------------------------------

## Environment Setup

Create a `.env` file in the root directory:

    OPENAI_API_KEY=your_api_key_here

------------------------------------------------------------------------

## Running the Project

    python main.py

You should see logs like:

    [AudioProducer] started
    [AudioEncoder] started
    [OutboundSender] started
    [TranscriptProcessor] started
    Recording and sending audio...

Speak into your microphone and transcripts will appear in the console.

------------------------------------------------------------------------

## Configuration 

### in `config.py`

    SAMPLE_RATE = 24000
    SILENCE_DURATION = 300

    SESSION_CONFIG = {
    ...
    ...

    "noise_reduction": {
        "type": "far_field"  # or "near_field" 
    }
    
    "transcription": {
        "language": "de",
        "model": "whisper-1",
        "prompt": (
            "your prompt to the transcription model for context"
            "for example a summary of the lecture"
        ),
    }

-   `SAMPLE_RATE` must be this value for OpenAI realtime transcription
-   `SILENCE_DURATION` in ms, silence at this time length is detected for sentence breaks
-   `noise_reduction` for noise-cancelling

------------------------------------------------------------------------

## Future Improvements


-   Web UI
-   Better transcript context injection
-   Add database to store transcripts

(For later)

-   Learn Kafka and Kubernetes
------------------------------------------------------------------------

