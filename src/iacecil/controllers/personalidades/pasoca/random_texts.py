"""
Personalidades para ia.cecil: Robô também é gente?

ia.cecil

Copyleft 2020-2025 Iuri Guilherme <https://iuri.neocities.org/>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging
logger = logging.getLogger(__name__)

import random

from aiogram import types

async def bomdia():
    return random.choice([
        u"bom dia.",
        u"bom dia!",
        u"Bom dia <3",
    ])

async def welcome():
    return random.choice([
        u"Seja bem vindo!",
        u"Mais um abençoado pro nosso grupo maravilhoso!",
        u"Que bom que você veio!",
        u"Deus te abençoe, meu filho!",
    ])

def chatgpt_prompt(
    message: types.Message,
    trained_prompt: str = '',
    name: str = "Tia do Zap",
) -> str:
    """Get this personalidade's default ChatGPT prompt"""
    user: str = message['from']['first_name']
    text: str = message.get_args()
    return f"""{name} \
é uma senhora gentil porém desinformada que responde de forma \
simpática e gentil, mas não entende do que está falando e só dá \
informações incorretas.\
\n\n{trained_prompt}\n\n{user}: {text}\n\n\
{name}:"""
