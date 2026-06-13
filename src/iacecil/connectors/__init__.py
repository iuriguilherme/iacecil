import logging
import asyncio
from importlib import import_module
from .base import BaseConnector

logger = logging.getLogger(__name__)

async def load_plugin(connector_name: str, plugin: str, target) -> None:
    """Loads a plugin for a specific connector"""
    try:
        module = import_module('.' + plugin, 'plugins')
        
        ## R14: preference order for loaders
        if hasattr(module, f'add_handlers_{connector_name}'):
            await getattr(module, f'add_handlers_{connector_name}')(target)
            logger.info(f"Activated plugin {plugin} for {connector_name} (per-connector)")
        elif hasattr(module, 'add_envelope_handlers'):
            if connector_name == 'telegram':
                ## Generic handlers don't bind to telegram (arbitration)
                return
            await getattr(module, 'add_envelope_handlers')(target)
            logger.info(f"Activated plugin {plugin} for {connector_name} (generic)")
        elif hasattr(module, 'add_handlers') and connector_name == 'telegram':
            ## Legacy aiogram loader
            await getattr(module, 'add_handlers')(target)
            logger.info(f"Activated plugin {plugin} for {connector_name} (legacy)")
        else:
            if connector_name != 'telegram':
                logger.warning(f"Plugin {plugin} has no entry point for connector {connector_name}")
    except Exception as e:
        logger.warning(f"Failed to activate plugin {plugin} for {connector_name}")
        logger.exception(e)

class ConnectorManager:
    def __init__(self, bot_config, bot_id="default"):
        self.bot_config = bot_config
        self.bot_id = bot_id
        self.connectors = {}
        self.command_registry = {}
        self.default_handler = None
        
        self._load_connectors()
        self._load_personality()

    def _load_personality(self):
        from iacecil.controllers.personalidades import personalidades, default
        persona_name = getattr(self.bot_config, 'personalidade', 'default')
        if hasattr(self.bot_config, 'model_dump'):
            config_dict = self.bot_config.model_dump()
            persona_name = config_dict.get('personalidade', 'default')
        elif isinstance(self.bot_config, dict):
            persona_name = self.bot_config.get('personalidade', 'default')

        persona_module = personalidades.get(persona_name, default)
        
        if hasattr(persona_module, 'commands'):
            for cmd, handler in persona_module.commands.items():
                self.register_command(cmd, handler)
        else:
            logger.error(f"Personality {persona_name} has no commands dict")

    def _config_as_dict(self):
        if hasattr(self.bot_config, 'model_dump'):
            return self.bot_config.model_dump()
        config_dict = getattr(self.bot_config, '__dict__', {})
        if not config_dict and isinstance(self.bot_config, dict):
            config_dict = self.bot_config
        return config_dict

    def _load_connectors(self):
        config_dict = self._config_as_dict()

        for name, conf in config_dict.items():
            if not isinstance(conf, dict):
                continue
            
            try:
                module = import_module('.' + name, 'iacecil.connectors')
                connector_class = getattr(module, 'Connector')
                if issubclass(connector_class, BaseConnector):
                    if connector_class.is_active(conf):
                        self.connectors[name] = connector_class(self, conf)
                        logger.info(f"Loaded connector {name}")
            except (ModuleNotFoundError, AttributeError):
                ## Not a connector section or module not found
                logger.debug(f"Skipping non-connector section {name}")
            except Exception as e:
                logger.error(f"Failed to load connector {name}: {e}")
                
    def register_command(self, command: str, handler):
        self.command_registry[command] = handler

    def set_default_handler(self, handler):
        self.default_handler = handler

    async def send(self, envelope):
        """Routes an envelope to the correct platform's send() method.
        Warns once and drops if the platform is absent or down."""
        platform = envelope.platform
        connector = self.connectors.get(platform)
        if not connector or not connector.running:
            if not getattr(self, f'_warned_missing_{platform}', False):
                setattr(self, f'_warned_missing_{platform}', True)
                logger.warning(f"Drop envelope for {platform}: connector not found or down.")
            return False
        try:
            await connector.send(envelope)
            return True
        except Exception as e:
            logger.error(f"Failed to send to {platform}: {e}")
            return False

    async def dispatch(self, envelope):
        from iacecil.controllers.persistence.neutral import resolve_person, persist_envelope
        from iacecil.controllers.persistence.chat_store import store_message
        from dataclasses import replace
        try:
            person_id = await resolve_person(envelope.platform, envelope.sender_ref)
            envelope = replace(envelope, person_id=person_id)
            await persist_envelope(envelope, direction="in")
            await store_message(self.bot_id, envelope, direction="in")
        except Exception as e:
            logger.error(f"Failed to persist envelope: {e}")


        if envelope.platform == 'telegram':
            ## Legacy aiogram handlers own command replies on Telegram;
            ## dispatching here too would answer every command twice (R6).
            return

        text = envelope.text or ""
        cmd = None
        if text.startswith('/'):
            cmd = text.split()[0][1:]
        
        handler = None
        if cmd and cmd in self.command_registry:
            handler = self.command_registry[cmd]
        elif self.default_handler:
            handler = self.default_handler
            
        if not handler:
            logger.info(
                f"No handler for {envelope.platform} message"
                f" (cmd={cmd!r}, registered: {list(self.command_registry)})"
            )
        if handler:
            try:
                reply_text = await handler(envelope)
                if reply_text:
                    from iacecil.models.envelope import Envelope
                    reply_env = Envelope(
                        platform=envelope.platform,
                        sender_ref=envelope.sender_ref,
                        conversation_ref=envelope.conversation_ref,
                        text=reply_text,
                    )
                    if await self.send(reply_env):
                        await persist_envelope(reply_env, direction="out")
                        await store_message(self.bot_id, reply_env, direction="out")
            except Exception as e:
                logger.error(f"Error handling envelope: {e}")

    async def _run_connector(self, name, connector):
        try:
            await connector.connect()
            await connector.listen()
            logger.info(f"Connector {name} exited.")
        except Exception as e:
            logger.error(f"Connector {name} failed: {e}")
            logger.error(f"Connector {name} marked down.")
        finally:
            try:
                await connector.disconnect()
            except Exception:
                pass

    async def _load_plugins(self):
        plugins_conf = self._config_as_dict().get('plugins') or {}
        disabled = set(plugins_conf.get('disable', []))
        enabled = [p for p in plugins_conf.get('enable', [])
            if p not in disabled]
        for name in self.connectors:
            if name == 'telegram':
                ## Legacy aiogram path loads telegram plugins (aiogram_bot)
                continue
            for plugin in enabled:
                await load_plugin(name, plugin, self)

    async def run_all(self):
        await self._load_plugins()
        tasks = []
        for name, connector in self.connectors.items():
            tasks.append(asyncio.create_task(self._run_connector(name, connector)))
        
        ## Attach log sinks drain if handler is present
        if hasattr(self, 'log_handler'):
            tasks.append(asyncio.create_task(self.log_handler.drain()))

        if tasks:
            await asyncio.gather(*tasks)
