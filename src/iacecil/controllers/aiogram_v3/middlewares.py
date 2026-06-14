"""
ia.cecil - aiogram 3 middlewares for dependency injection
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from contextvars import ContextVar

## ContextVar for global access in utility functions (like logging)
## inside a handler task.
manager_context: ContextVar[Any] = ContextVar("manager_context", default=None)
config_context: ContextVar[Any] = ContextVar("config_context", default=None)
dispatcher_context: ContextVar[Any] = ContextVar("dispatcher_context", default=None)

class ContextMiddleware(BaseMiddleware):
    def __init__(self, manager: Any, bot_config: Any, connector_config: Any):
        self.manager = manager
        self.bot_config = bot_config
        self.connector_config = connector_config

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        ## Inject into handler arguments
        data["manager"] = self.manager
        data["bot_config"] = self.bot_config
        data["connector_config"] = self.connector_config
        
        ## Set contextvars for utility functions
        t_manager = manager_context.set(self.manager)
        t_config = config_context.set(self.bot_config)
        
        ## Try to find dispatcher in data (aiogram 3 usually puts it there)
        dp = data.get("dispatcher")
        t_dispatcher = dispatcher_context.set(dp)
        
        try:
            return await handler(event, data)
        finally:
            ## Reset contextvars
            manager_context.reset(t_manager)
            config_context.reset(t_config)
            dispatcher_context.reset(t_dispatcher)
