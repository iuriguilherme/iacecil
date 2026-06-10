from abc import ABC, abstractmethod
from iacecil.models.envelope import Envelope

class BaseConnector(ABC):
    def __init__(self, manager, config):
        self.manager = manager
        self.config = config

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
