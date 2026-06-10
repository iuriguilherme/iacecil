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
