from abc import ABC, abstractmethod
from iacecil.models.envelope import Envelope

class BaseConnector(ABC):
    ## Activation contract: a connector activates for a bot iff its
    ## config section satisfies the class' own rule. Subclasses either
    ## list required_keys (all must be truthy in the section) or
    ## override is_active() for richer rules. The manager never
    ## hardcodes per-platform credential checks.
    required_keys: tuple = ()

    ## Largest text payload one send may carry on this platform;
    ## connectors chunk outbound text at this bound. Falsy means no
    ## platform limit.
    MAX_TEXT: int = 0

    def __init__(self, manager, config):
        self.manager = manager
        self.config = config
        self.running: bool = False

    @classmethod
    def is_active(cls, conf: dict) -> bool:
        if not conf:
            return False
        return all(conf.get(key) for key in cls.required_keys)

    def _chunks(self, text: str):
        """Yield text in MAX_TEXT-sized pieces (one piece when MAX_TEXT is
        falsy / no platform limit). Centralizes the chunking arithmetic
        every connector's send() shares; each connector keeps its own
        per-chunk delivery (reply refs, content envelopes, etc.)."""
        text = text or ""
        if not self.MAX_TEXT:
            yield text
            return
        for i in range(0, len(text), self.MAX_TEXT):
            yield text[i:i + self.MAX_TEXT]

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def listen(self):
        pass

    @abstractmethod
    async def send(self, envelope: Envelope):
        pass

    @abstractmethod
    async def disconnect(self):
        pass
