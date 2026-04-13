import json
import queue
import threading
import time

from models import EncodedAudioMessage, OutboundMessage
from time_utils import now_ts, ms_between


class OutboundSender:
    def __init__(self, ws, encoded_audio_queue: queue.Queue, control_queue: queue.Queue):
        """
        :param ws:
        :param encoded_audio_queue:
        :param control_queue:
        """
        self.ws = ws
        self.encoded_audio_queue = encoded_audio_queue
        self.control_queue = control_queue
        self.running = False
        self.thread = None
        self.total_audio_sent = 0

    def start(self):
        """
        starts the websocket sender
        """
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("[OutboundSender] started", flush=True)

    def stop(self):
        """
        stops the websocket sender
        :return:
        """
        self.running = False

    def _send_json(self, payload: dict):
        self.ws.send(json.dumps(payload))

    def _run(self):
        while self.running:
            # # control messages first
            # try:
            #     msg: OutboundMessage = self.control_queue.get(timeout=0.02)
            #     self._send_json(msg.payload)
            #     continue
            # except queue.Empty:
            #     pass
            # except Exception as e:
            #     print(f"[OutboundSender] control send failed: {e}", flush=True)
            #     time.sleep(0.2)
            #     continue

            # then audio messages
            try:
                msg: EncodedAudioMessage = self.encoded_audio_queue.get(timeout=0.02)
            except queue.Empty:
                continue

            try:
                sent_at = now_ts()
                encode_to_send_ms = ms_between(msg.encoded_at, sent_at)
                capture_to_send_ms = ms_between(msg.captured_at, sent_at)

                self._send_json(msg.payload)

                self.total_audio_sent += 1
                if self.total_audio_sent % 25 == 0:
                    print(
                        f"[OutboundSender] sent seq={msg.seq}, "
                        f"encode->send={encode_to_send_ms} ms, "
                        f"capture->send={capture_to_send_ms} ms, "
                        f"total_sent={self.total_audio_sent}",
                        flush=True,
                    )
            except Exception as e:
                print(f"[OutboundSender] audio send failed: {e}", flush=True)
                time.sleep(0.2)