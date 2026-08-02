import datetime as dt
from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()
