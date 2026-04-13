import base64
import queue
import threading

from models import AudioChunk, EncodedAudioMessage
from time_utils import now_ts, ms_between


class AudioEncoder:
    def __init__(self, raw_audio_queue: queue.Queue, encoded_audio_queue: queue.Queue):
        """
        :param raw_audio_queue: the raw audio data that needs to be encoded
        :param encoded_audio_queue: the queue where the encoded messages are put into
        """
        self.raw_audio_queue = raw_audio_queue
        self.encoded_audio_queue = encoded_audio_queue
        self.running = False
        self.thread = None
        self.total_encoded = 0

    def start(self):
        """
        Start the audio encoder
        """
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("[AudioEncoder] started", flush=True)

    def stop(self):
        """
        Stop the audio encoder
        """
        self.running = False

    def _run(self):
        while self.running:
            try:
                chunk: AudioChunk = self.raw_audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            encoded_at = now_ts()
            audio_b64 = base64.b64encode(chunk.data).decode("ascii")

            message = EncodedAudioMessage(
                seq=chunk.seq,
                captured_at=chunk.captured_at,
                encoded_at=encoded_at,
                payload={
                    "type": "input_audio_buffer.append",
                    "audio": audio_b64,
                },
            )

            try:
                self.encoded_audio_queue.put_nowait(message)
            except queue.Full:
                # if queue is full, drop the oldest block
                try:
                    _ = self.encoded_audio_queue.get_nowait()
                except queue.Empty:
                    pass

                # try to put the message inside again
                try:
                    self.encoded_audio_queue.put_nowait(message)
                except queue.Full:
                    pass

            self.total_encoded += 1
            if self.total_encoded % 25 == 0:
                capture_to_encode_ms = ms_between(chunk.captured_at, encoded_at)
                print(
                    f"[AudioEncoder] encoded seq={chunk.seq}, "
                    f"capture->encode={capture_to_encode_ms} ms, "
                    f"total_encoded={self.total_encoded}",
                    flush=True,
                )