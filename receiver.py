import json
import queue

from time_utils import now_ts


class WebSocketReceiver:
    def __init__(self, event_queue: queue.Queue, log_queue: queue.Queue | None = None):
        """
        :param event_queue: listening for websocket events
        :param log_queue:
        """
        self.event_queue = event_queue
        self.log_queue = log_queue

    def on_message(self, ws, message: str):
        received_at = now_ts()

        try:
            event = json.loads(message)
        except json.JSONDecodeError as e:
            print(f"[Receiver] invalid JSON: {e}", flush=True)
            return

        event["_client_received_at"] = received_at

        if self.log_queue is not None:
            try:
                self.log_queue.put_nowait(message)
            except queue.Full:
                pass

        try:
            self.event_queue.put_nowait(event)
        except queue.Full:
            print("[Receiver] event queue full, dropping event", flush=True)

    def on_error(self, ws, error):
        print(f"[Receiver] websocket error: {error}", flush=True)

    def on_close(self, ws, status_code, close_msg):
        print(f"[Receiver] websocket closed: code={status_code}, msg={close_msg}", flush=True)