from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

@dataclass(frozen=True)
class Envelope:
    platform: str
    sender_ref: str
    conversation_ref: str
    text: str
    reply_ref: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    raw: Any = field(default=None, repr=False)
    extra: Dict[str, Any] = field(default_factory=dict)
    ## Platform-assigned message id, when the platform exposes one
    ## (telegram message_id, matrix event id, discord snowflake).
    native_message_id: Optional[str] = None
    ## Unix epoch seconds (UTC). Persistence fills in "now" when the
    ## platform supplied none.
    timestamp: Optional[float] = None
    ## Canonical Person id from persistence/neutral.py. Resolved
    ## during dispatch.
    person_id: Optional[str] = None
