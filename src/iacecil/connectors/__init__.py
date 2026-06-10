import logging
import asyncio
from importlib import import_module
from .base import BaseConnector

logger = logging.getLogger(__name__)

class ConnectorManager:
    def __init__(self, bot_config):
        self.bot_config = bot_config
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

    def _is_active(self, name, conf):
        if not conf:
            return False
        if name == 'telegram':
            return bool(conf.get('token'))
        elif name == 'xmpp':
            return bool(conf.get('jid') and conf.get('password'))
        elif name == 'loopback':
            return bool(conf.get('enabled'))
        elif name == 'discord':
            return bool(conf.get('token'))
        return True

    def _load_connectors(self):
        if hasattr(self.bot_config, 'model_dump'):
            config_dict = self.bot_config.model_dump()
        else:
            config_dict = getattr(self.bot_config, '__dict__', {})
            if not config_dict and isinstance(self.bot_config, dict):
                config_dict = self.bot_config

        allowed_connectors = {'telegram', 'xmpp', 'loopback', 'discord'}
        
        for name, conf in config_dict.items():
            if name in allowed_connectors and isinstance(conf, dict):
                if self._is_active(name, conf):
                    self._load_connector(name, conf)
            elif name not in allowed_connectors and isinstance(conf, dict) and conf.get('token'):
                logger.error(f"Unknown connector section '{name}' with credentials, skipping.")
                
    def _load_connector(self, name: str, config: dict):
        try:
            module = import_module('.' + name, 'iacecil.connectors')
            connector_class = getattr(module, 'Connector')
            self.connectors[name] = connector_class(self, config)
            logger.info(f"Loaded connector {name}")
        except ModuleNotFoundError:
            logger.error(f"Module for connector {name} not found.")
        except Exception as e:
            logger.error(f"Failed to load connector {name}: {e}")

    def register_command(self, command: str, handler):
        self.command_registry[command] = handler

    def set_default_handler(self, handler):
        self.default_handler = handler

    async def dispatch(self, envelope):
        from iacecil.controllers.persistence.neutral import persist_envelope, resolve_person
        try:
            await resolve_person(envelope.platform, envelope.sender_ref)
            await persist_envelope(envelope)
        except Exception as e:
            logger.error(f"Failed to persist envelope: {e}")

        text = envelope.text or ""
        cmd = None
        if text.startswith('/'):
            cmd = text.split()[0][1:]
        
        handler = None
        if cmd and cmd in self.command_registry:
            handler = self.command_registry[cmd]
        elif self.default_handler:
            handler = self.default_handler
            
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
                    await self.connectors[envelope.platform].send(reply_env)
            except Exception as e:
                logger.error(f"Error handling envelope: {e}")

    async def _run_connector(self, name, connector):
        try:
            await connector.connect()
            await connector.listen()
        except Exception as e:
            logger.error(f"Connector {name} failed: {e}")
        finally:
            logger.error(f"Connector {name} marked down.")
            if name in self.connectors:
                try:
                    await connector.disconnect()
                except:
                    pass

    async def run_all(self):
        tasks = []
        for name, connector in self.connectors.items():
            tasks.append(asyncio.create_task(self._run_connector(name, connector)))
        if tasks:
            await asyncio.gather(*tasks)
