"""
ia.cecil - aiogram context utilities
"""

import logging
logger = logging.getLogger(__name__)

from typing import Any, Dict
from aiogram import Dispatcher

def get_aiogram_context() -> Dict[str, Any]:
    """
    Safely retrieves aiogram context (bot, dispatcher, config, manager) 
    from either modern ContextVars or legacy get_current().
    """
    ctx = {'bot': None, 'dispatcher': None, 'config': None, 'manager': None}
    
    ## 1. Try modern V3 ContextVars
    try:
        from .middlewares import config_context, manager_context, dispatcher_context
        
        modern_config = config_context.get()
        if modern_config:
            ctx['config'] = modern_config
        
        modern_manager = manager_context.get()
        if modern_manager:
            ctx['manager'] = modern_manager
            
        modern_dispatcher = dispatcher_context.get()
        if modern_dispatcher:
            ctx['dispatcher'] = modern_dispatcher
            
        ## Bot Retrieval Priority:
        ## 1. On Dispatcher (we set it in startup)
        if ctx['dispatcher'] and hasattr(ctx['dispatcher'], 'bot'):
            ctx['bot'] = ctx['dispatcher'].bot
        ## 2. On Config (if it's a dict or has the attribute)
        elif ctx['config']:
            if hasattr(ctx['config'], 'bot'):
                ctx['bot'] = ctx['config'].bot
            elif isinstance(ctx['config'], dict) and 'bot' in ctx['config']:
                ctx['bot'] = ctx['config']['bot']
        ## 3. Via Manager connectors
        elif ctx['manager'] and hasattr(ctx['manager'], 'connectors'):
            for connector in ctx['manager'].connectors.values():
                if hasattr(connector, 'bot') and connector.bot:
                    ctx['bot'] = connector.bot
                    break
            
        if modern_config or modern_manager or modern_dispatcher:
            return ctx
    except (ImportError, LookupError):
        pass

    ## 2. Try Quart current_app
    try:
        from quart import current_app
        if current_app:
            ## In our setup, dispatchers are attached to current_app
            dispatchers = getattr(current_app, 'dispatchers', [])
            if dispatchers:
                ctx['dispatcher'] = dispatchers[0]
                ctx['bot'] = getattr(dispatchers[0], 'bot', None)
                ctx['config'] = getattr(dispatchers[0], 'config', None)
                ctx['manager'] = getattr(dispatchers[0], 'manager', None)
                return ctx
    except (ImportError, RuntimeError, AttributeError):
        pass

    ## 3. Try legacy Dispatcher.get_current()
    try:
        dispatcher = Dispatcher.get_current()
        if dispatcher:
            ctx['dispatcher'] = dispatcher
            ctx['bot'] = getattr(dispatcher, 'bot', None)
            ctx['config'] = getattr(dispatcher, 'config', None)
            ctx['manager'] = getattr(dispatcher, 'manager', None)
            return ctx
    except (AttributeError, RuntimeError):
        pass
        
    return ctx
