import asyncio
import sys
from .base import BaseConnector
from iacecil.models.envelope import Envelope

class Connector(BaseConnector):
    def __init__(self, manager, config):
        super().__init__(manager, config)
        self.queue = asyncio.Queue()
        self.running = False
        self._reader_task = None
        
    async def connect(self):
        self.running = True

    async def listen(self):
        loop = asyncio.get_event_loop()
        
        async def stdin_reader():
            while self.running:
                try:
                    line = await loop.run_in_executor(None, sys.stdin.readline)
                    if not line:
                        break
                    text = line.strip()
                    if text:
                        await self.inject(text)
                except Exception:
                    break
        
        if "pytest" not in sys.modules:
            self._reader_task = asyncio.create_task(stdin_reader())
            
        while self.running:
            text = await self.queue.get()
            if text is None:
                break
            env = Envelope(
                platform='loopback',
                sender_ref='local_user',
                conversation_ref='local_chat',
                text=text
            )
            await self.manager.dispatch(env)

    async def inject(self, text):
        await self.queue.put(text)
        
    async def send(self, envelope: Envelope):
        print(f"> {envelope.text}")

    async def disconnect(self):
        self.running = False
        await self.queue.put(None)
        if self._reader_task:
            self._reader_task.cancel()
