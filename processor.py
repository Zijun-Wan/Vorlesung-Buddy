import queue
import threading
from collections import deque

from models import OutboundMessage
from time_utils import fmt_ts, ms_between, now_ts


class TranscriptProcessor:
    def __init__(self, event_queue: queue.Queue, control_queue: queue.Queue):
        self.event_queue = event_queue
        self.control_queue = control_queue

        self.running = False
        self.thread = None

        self.previous_item_id = None
        self.expected_ids = deque()
        self.pending_transcripts = {}
        self.silence_duration = 300

        # timestamps / metrics per item_id
        self.item_created_at = {}
        self.item_added_at = {}
        self.item_completed_at = {}

        # stats
        self.total_transcripts = 0

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("[TranscriptProcessor] started", flush=True)

    def stop(self):
        self.running = False

    def _run(self):
        while self.running:
            try:
                event = self.event_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                self._handle_event(event)
            except Exception as e:
                print(f"[TranscriptProcessor] handler error: {e}", flush=True)

    def _handle_event(self, event: dict):
        event_type = event.get("type")

        if event_type == "input_audio_buffer.speech_started":
            self._handle_item_created(event)
            return

        # new conversation started, the previous id and item id are tracking the correct order, also this event always happens in order (hopefully?!
        if event_type == "conversation.item.added":
            self._handle_item_added(event)
            return

        # transcription received, but need to print the transcriptions in the expected queue before printing this one
        if event_type == "conversation.item.input_audio_transcription.completed":
            self._handle_transcription_completed(event)
            return

        if event_type == "error":
            err = event.get("error", {}).get("message", "Unknown error")
            print(f"[Server Error] {err}", flush=True)
            return

    def _handle_item_created(self, event: dict):
        item_id = event.get("item_id")
        received_at = event.get("_client_received_at", now_ts())

        if item_id is None:
            return

        self.item_created_at[item_id] = received_at

    def _handle_item_added(self, event: dict):
        prev = event.get("previous_item_id")
        item = event.get("item", {})
        item_id = item.get("id")
        received_at = event.get("_client_received_at", now_ts())

        if item_id is None:
            print("[TranscriptProcessor] item.added without item.id", flush=True)
            return

        self.item_added_at[item_id] = received_at

        if self.previous_item_id is None or prev == self.previous_item_id:
            self.expected_ids.append(item_id)
            self.previous_item_id = item_id
        else:
            print(
                f"[TranscriptProcessor] ordering gap on item.added: "
                f"expected prev={self.previous_item_id}, got prev={prev}",
                flush=True,
            )

    def _handle_transcription_completed(self, event: dict):
        item_id = event.get("item_id")
        transcript = event.get("transcript", "")
        received_at = event.get("_client_received_at", now_ts())

        if not item_id:
            print("[TranscriptProcessor] completed event without item_id", flush=True)
            return

        self.item_completed_at[item_id] = received_at

        # TODO: improve order handling? e.g. Timeout-based skipping
        if self.expected_ids and item_id == self.expected_ids[0]:
            self.expected_ids.popleft()
            self._emit_transcript(item_id, transcript)
            self._flush_ready_pending()
        else:
            self.pending_transcripts[item_id] = transcript

    def _flush_ready_pending(self):
        while self.expected_ids and self.expected_ids[0] in self.pending_transcripts:
            next_id = self.expected_ids.popleft()
            transcript = self.pending_transcripts.pop(next_id)
            print("[TranscriptProcessor] found pending transcript in correct order", flush=True)
            self._emit_transcript(next_id, transcript)

    def _emit_transcript(self, item_id: str, transcript: str):
        completed_at = self.item_completed_at.get(item_id)
        created_at = self.item_created_at.get(item_id)
        added_at = self.item_added_at.get(item_id)

        created_to_completed_ms = ms_between(created_at, completed_at)
        added_to_completed_ms = ms_between(added_at, completed_at)

        self.total_transcripts += 1

        print("\n" + "=" * 80, flush=True)
        print(f"[Transcript #{self.total_transcripts}]", flush=True)
        # print(f"item_id: {item_id}", flush=True)
        # print(f"created_at:   {fmt_ts(created_at)}", flush=True)
        # print(f"added_at:     {fmt_ts(added_at)}", flush=True)
        # print(f"completed_at: {fmt_ts(completed_at)}", flush=True)
        print(f"created->completed: {created_to_completed_ms} ms", flush=True)
        print(f"added->completed:   {added_to_completed_ms} ms", flush=True)
        # print(f"word_count: {len(transcript.split())}", flush=True)
        print(f"text: {transcript}", flush=True)

        print(f"item count in event_queue: {self.event_queue.qsize()}", flush=True)
        print("=" * 80 + "\n", flush=True)

        # optional adaptive VAD logic
        # n = len(transcript.split())
        # if n <= 5 or n >= 25:
        #     self._adjust_silence_duration(n)

        self._cleanup_item(item_id)

    def _cleanup_item(self, item_id: str):
        self.item_created_at.pop(item_id, None)
        self.item_added_at.pop(item_id, None)
        self.item_completed_at.pop(item_id, None)

    def _adjust_silence_duration(self, sentence_length: int):
        if sentence_length <= 5:
            self.silence_duration += (2000 - self.silence_duration) * 0.3
        elif sentence_length >= 25:
            self.silence_duration -= (self.silence_duration - 200) * 0.3

        self.silence_duration = int(max(200, min(2000, self.silence_duration)))
        print(f"[TranscriptProcessor] new silence duration: {self.silence_duration} ms", flush=True)

        self.control_queue.put(
            OutboundMessage(
                payload={
                    "type": "session.update",
                    "session": {
                        "type": "transcription",
                        "audio": {
                            "input": {
                                "turn_detection": {
                                    "type": "server_vad",
                                    "silence_duration_ms": self.silence_duration,
                                }
                            }
                        },
                    },
                }
            )
        )