import queue
import sounddevice as sd

from config import SAMPLE_RATE
from models import AudioChunk
from time_utils import now_ts


class AudioRecorder:
    def __init__(self, raw_audio_queue: queue.Queue, max_drops_to_log: int = 20):
        """
        :param raw_audio_queue: queue for raw audio bytes
        """
        self.raw_audio_queue = raw_audio_queue
        self.seq = 0
        self.stream = None
        self.drop_count = 0
        # self.max_drops_to_log = max_drops_to_log

    def _callback(self, indata, frames, time, status):
        """
        callback that runs whenever an input block is ready
        """
        if status:
            print(f"[Audio status] {status}", flush=True)

        chunk = AudioChunk(
            seq=self.seq,
            captured_at=now_ts(), # time.inputBufferAdcTime
            data=bytes(indata),
        )
        self.seq += 1

        try:
            self.raw_audio_queue.put_nowait(chunk)
        except queue.Full:
            self.drop_count += 1
            # if queue is full, drop the oldest block
            try:
                _ = self.raw_audio_queue.get_nowait()
            except queue.Empty:
                pass

            # try to put the data inside again
            try:
                self.raw_audio_queue.put_nowait(chunk)
            except queue.Full:
                pass

            # if self.drop_count <= self.max_drops_to_log:
            print(f"[AudioRecorder] dropped chunk, total drops={self.drop_count}", flush=True)
            # try this later
            # print("queue size:", q.qsize())

    def start(self):
        """
        starts the audio recorder
        """
        self.stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=2400,   # ~100 ms at 24 kHz, try 1200 later
            dtype="int16",
            channels=1,
            callback=self._callback,
        )
        self.stream.start()
        print("[AudioRecorder] microphone stream started", flush=True)

    def stop(self):
        """
        stops the audio recorder
        """
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            print("[AudioRecorder] microphone stream stopped", flush=True)