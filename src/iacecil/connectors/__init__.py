import logging
import asyncio
from importlib import import_module
from .base import BaseConnector

logger = logging.getLogger(__name__)

async def load_plugin(connector_name: str, plugin: str, target) -> None:
    """Loads a plugin for a specific connector.

    Importing a plugin module has no side effects; registration happens
    only through loader functions. Resolution order per connector:
    the per-connector loader (``add_handlers_<connector>``) wins over
    the generic envelope loader (``add_envelope_handlers``). Bare
    ``add_handlers`` remains the aiogram/telegram legacy loader.
    """
    try:
        module = import_module('.' + plugin, 'plugins')
        if connector_name == 'telegram':
            entry_names = ['add_handlers']
        else:
            entry_names = [
                f'add_handlers_{connector_name}',
                'add_envelope_handlers',
            ]
        for entry_name in entry_names:
            if hasattr(module, entry_name):
                await getattr(module, entry_name)(target)
                logger.info(f"Activated plugin {plugin} for {connector_name}")
                return
        logger.warning(
            f"Plugin {plugin} has no entry point"
            f" {' or '.join(entry_names)} for connector {connector_name}"
        )
    except Exception as e:
        logger.warning(f"Failed to activate plugin {plugin} for {connector_name}")
        logger.exception(e)

class ConnectorManager:
    def __init__(self, bot_config, bot_id: str = "default"):
        self.bot_config = bot_config
        ## Bot config name; keys per-bot storage and logging. The
        ## connectors runner passes the instance/bots/<name> config
        ## name; the loopback REPL and legacy paths use the default.
        self.bot_id = bot_id
        self.connectors = {}
        self.command_registry = {}
        self.default_handler = None
        self._send_warned_platforms = set()

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
        """Activate a connector for every config section whose module
        exists in this package and whose class reports active.

        Connectors declare their own activation rule (required_keys /
        is_active on the class); there is no allowlist. Config carries
        many non-connector dict sections (openai, coinmarketcap, ...),
        so a missing module is a quiet skip, while a module that exists
        but fails to import (e.g. missing platform library) is an
        error.
        """
        config_dict = self._config_as_dict()

        for name, conf in config_dict.items():
            if not isinstance(conf, dict):
                continue
            try:
                module = import_module('.' + name, 'iacecil.connectors')
            except ModuleNotFoundError as e:
                if e.name == f"iacecil.connectors.{name}":
                    logger.debug(
                        f"No connector module for config section '{name}',"
                        " skipping."
                    )
                else:
                    logger.error(
                        f"Connector {name} failed to import"
                        f" (missing dependency {e.name})."
                    )
                continue
            except Exception as e:
                logger.error(f"Connector {name} failed to import: {e}")
                continue
            connector_class = getattr(module, 'Connector', None)
            if connector_class is None:
                logger.debug(
                    f"Module iacecil.connectors.{name} has no Connector"
                    " class, skipping."
                )
                continue
            try:
                if connector_class.is_active(conf):
                    self.connectors[name] = connector_class(self, conf)
                    logger.info(f"Loaded connector {name}")
            except Exception as e:
                logger.error(f"Failed to load connector {name}: {e}")

    def register_command(self, command: str, handler):
        self.command_registry[command] = handler

    def set_default_handler(self, handler):
        self.default_handler = handler

    async def send(self, envelope) -> bool:
        """Route an outbound envelope to its platform's connector.

        Returns True on a dispatched send, False when the platform has
        no active connector (warned once per platform) or the send
        raised (logged). Never raises: callers like the log-sink drain
        must survive delivery failure.
        """
        connector = self.connectors.get(envelope.platform)
        if connector is None:
            if envelope.platform not in self._send_warned_platforms:
                self._send_warned_platforms.add(envelope.platform)
                logger.warning(
                    f"No active connector for platform"
                    f" {envelope.platform}; dropping message."
                )
            return False
        try:
            await connector.send(envelope)
            return True
        except Exception as e:
            logger.error(f"Failed to send via {envelope.platform}: {e}")
            return False

    async def dispatch(self, envelope):
        from iacecil.controllers.persistence.neutral import persist_envelope, resolve_person
        try:
            await resolve_person(envelope.platform, envelope.sender_ref)
            await persist_envelope(envelope, direction='in')
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
                    await self.send(reply_env)
                    try:
                        await persist_envelope(reply_env, direction='out')
                    except Exception as e:
                        logger.error(f"Failed to persist outbound envelope: {e}")
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
        if tasks:
            await asyncio.gather(*tasks)
