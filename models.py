from dataclasses import dataclass
from typing import Any


@dataclass
class AudioChunk:
    """
    Represents a chunk of raw audio data.
    """
    seq: int            # Sequence number
    captured_at: float  # Timestamp of capture
    data: bytes         # Raw audio bytes

@dataclass
class EncodedAudioMessage:
    seq: int
    captured_at: float
    encoded_at: float
    payload: dict[str, Any]

@dataclass
class OutboundMessage:
    payload: dict[str, Any]
