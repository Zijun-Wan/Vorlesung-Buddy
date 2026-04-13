import queue
import websocket

from auth import create_client_secret
from config import WS_URL
from audio_recorder import AudioRecorder
from audio_encoder import AudioEncoder
from sender import OutboundSender
from receiver import WebSocketReceiver
from processor import TranscriptProcessor
from logger import LogWorker

raw_audio_queue = queue.Queue(maxsize=120)
encoded_audio_queue = queue.Queue(maxsize=120)
control_queue = queue.Queue(maxsize=200)
event_queue = queue.Queue(maxsize=1000)
log_queue = queue.Queue(maxsize=2000)

audio_recorder = None
audio_encoder = None
sender = None

processor = TranscriptProcessor(event_queue=event_queue, control_queue=control_queue)
receiver = WebSocketReceiver(event_queue=event_queue, log_queue=log_queue)
logger = LogWorker(log_queue=log_queue)


def on_open(ws):
    global audio_recorder, audio_encoder, sender

    print("[Main] websocket connection opened", flush=True)

    sender = OutboundSender(
        ws=ws,
        encoded_audio_queue=encoded_audio_queue,
        control_queue=control_queue,
    )
    sender.start()

    audio_encoder = AudioEncoder(
        raw_audio_queue=raw_audio_queue,
        encoded_audio_queue=encoded_audio_queue,
    )
    audio_encoder.start()

    audio_producer = AudioRecorder(raw_audio_queue=raw_audio_queue)
    audio_producer.start()


def main():
    client_secret = create_client_secret()
    print("[Main] client secret created", flush=True)

    header = {
        "Authorization": f"Bearer {client_secret}",
    }

    logger.start()
    processor.start()

    ws = websocket.WebSocketApp(
        WS_URL,
        header=header,
        on_open=on_open,
        on_message=receiver.on_message,
        on_error=receiver.on_error,
        on_close=receiver.on_close,
    )

    ws.run_forever()


if __name__ == "__main__":
    main()