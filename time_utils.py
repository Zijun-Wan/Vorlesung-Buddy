from datetime import datetime, timezone


def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def fmt_ts(ts: float | None) -> str:
    if ts is None:
        return "-"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M:%S.%f")[:-3] + "Z"


def ms_between(start: float | None, end: float | None) -> int | None:
    if start is None or end is None:
        return None
    return int((end - start) * 1000)