import queue
import threading


class LogWorker:
    def __init__(self, log_queue: queue.Queue, filepath: str = "openai-log.txt"):
        self.log_queue = log_queue
        self.filepath = filepath
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("[LogWorker] started", flush=True)

    def stop(self):
        self.running = False

    def _run(self):
        with open(self.filepath, "a", encoding="utf-8") as f:
            while self.running:
                try:
                    line = self.log_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                f.write(line + "\n")
                f.flush()