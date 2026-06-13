import logging
import asyncio
from importlib import import_module
from .base import BaseConnector

logger = logging.getLogger(__name__)

async def load_plugin(connector_name: str, plugin: str, target) -> None:
    """Loads a plugin for a specific connector"""
    try:
        module = import_module('.' + plugin, 'plugins')
        
        ## R14 preference order:
        ##   1. per-connector loader  add_handlers_<connector>
        ##   2. telegram only: legacy aiogram add_handlers — the generic
        ##      add_envelope_handlers must NOT preempt it (strangler-fig
        ##      arbitration), so telegram is resolved before the generic tier.
        ##   3. generic add_envelope_handlers (non-telegram connectors only)
        if hasattr(module, f'add_handlers_{connector_name}'):
            await getattr(module, f'add_handlers_{connector_name}')(target)
            logger.info(f"Activated plugin {plugin} for {connector_name} (per-connector)")
        elif connector_name == 'telegram':
            if hasattr(module, 'add_handlers'):
                await getattr(module, 'add_handlers')(target)
                logger.info(f"Activated plugin {plugin} for {connector_name} (legacy)")
        elif hasattr(module, 'add_envelope_handlers'):
            await getattr(module, 'add_envelope_handlers')(target)
            logger.info(f"Activated plugin {plugin} for {connector_name} (generic)")
        else:
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
        ## Platforms we've already warned about as missing/down (send()).
        self._warned_missing = set()
        ## Set externally by the runner when log sinks are configured.
        self.log_handler = None

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
            if platform not in self._warned_missing:
                self._warned_missing.add(platform)
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
                    ## Carry person_id (and platform/refs) onto the reply so
                    ## the outbound record links to the triggering person;
                    ## null the inbound-only fields.
                    reply_env = replace(
                        envelope,
                        text=reply_text,
                        reply_ref=None,
                        raw=None,
                        native_message_id=None,
                        timestamp=None,
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
        
        ## Drain runs forever; keep it separate so it can be cancelled once
        ## the connectors exit — gathering it inline would hang run_all.
        drain_task = None
        if self.log_handler is not None:
            drain_task = asyncio.create_task(self.log_handler.drain())

        if not tasks:
            return
        try:
            ## return_exceptions so one connector's failure cannot cancel
            ## its siblings (per-connector isolation, R2).
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            if drain_task is not None:
                drain_task.cancel()
                try:
                    await drain_task
                except asyncio.CancelledError:
                    pass
