"""Who the bots are, according to configuration.

The web unit used to learn this from live aiogram dispatchers in its own
process (`dispatcher.bot.get_me()`). Once the connectors run in their
own process there are no dispatchers to ask, so identity comes from the
same `instance/` configuration the connector unit reads (R8, R10).

The shape mirrors what `get_me()` returned — `id`, `first_name`,
`username` — so the templates and routes that consume it do not have to
change their field names. What it cannot know is live state: whether a
bot is currently polling is connector-process knowledge, and slice 2's
control channel is what will answer it.

Copyleft 2012-2026 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
"""

import logging

logger = logging.getLogger(__name__)


def bot_id_from_token(token) -> str:
    """A telegram token is `<bot id>:<secret>`; keep only the id.

    The secret never leaves configuration — the id is the part the web
    unit shows and keys storage by.
    """
    if not token:
        return ''
    return str(token).split(':', 1)[0]


def identity_from_config(bot_name: str, config) -> dict:
    """One bot's identity, in the shape `get_me()` used to return."""
    telegram = getattr(config, 'telegram', None) or {}
    info = getattr(config, 'info', None) or {}
    bot_id = bot_id_from_token(telegram.get('token'))
    return {
        'id': bot_id,
        'name': bot_name,
        'first_name': info.get('first_name', bot_name),
        'username': info.get('username', bot_name),
        ## Live state belongs to the connector process; slice 2's control
        ## channel answers it. Never guess it here.
        'status': None,
    }


def build_bot_identities(configs: dict) -> list:
    """Identities for every configured bot, in configuration order."""
    identities = []
    for bot_name, config in (configs or {}).items():
        try:
            identities.append(identity_from_config(bot_name, config))
        except Exception as exception:
            ## One malformed bot config must not blank the whole page.
            logger.warning(
                f"Could not read identity for bot {bot_name}: {exception!r}")
    return identities
