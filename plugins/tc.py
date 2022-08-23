# vim:fileencoding=utf-8
"""Plugin tc para ia.cecil"""

#  Copyleft (C) 2022 Iuri Guilherme <https://iuri.neocities.org/>
#  
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  

import logging
logger = logging.getLogger(__name__)

import numpy
import random
from aiogram import filters
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from matplotlib import pyplot
from io import BytesIO
from iacecil import (
    commit,
    version,
)
from iacecil.controllers.aiogram_bot.callbacks import (
    command_callback,
    error_callback,
    message_callback,
)
from iacecil.controllers.persistence.zodb_orm import (
    get_tc_levels,
    set_tc_level,
    set_tc_roll,
)
from plugins.mate_matica import dice

## Valores padrão
faces = 6
comando = '/torre'
icones = [
    u"\U00002764",
    u"\U0001f9e1",
    u"\U0001f49b",
    u"\U0001f49a",
    u"\U0001f499",
    u"\U0001f49c",
    u"\U0001f5a4",
    u"\U0001f90d",
    u"\U0001f90e",
    # ~ 'A',
    # ~ 'B',
    # ~ 'C',
    # ~ 'D',
    # ~ 'E',
    # ~ 'F',
    # ~ 'G',
]

async def level_down(bot_id: str, user_id: str, levels: list) -> int:
    level = max(0, levels[-1] - 1)
    await set_tc_level(bot_id, user_id, level)
    return (level, 0)

async def level_up(bot_id: str, user_id: str, levels: list) -> int:
    level = levels[-1] + 1
    await set_tc_level(bot_id, user_id, level)
    return (level, 0)

async def levels_up(bot_id: str, user_id: str, levels: list) -> int:
    roll = dice(faces)
    level = levels[-1] + roll
    await set_tc_level(bot_id, user_id, level)
    return (level, roll)

mapa = {
    1: level_down,
    2: level_down,
    3: level_down,
    4: level_up,
    5: level_up,
    6: levels_up,
}

async def add_handlers(dispatcher):
    """
    Registra handlers em um Aiogram Dispatcher caso este plugin esteja
    habilitado.
    """
    try:
        @dispatcher.message_handler(
            commands = ['torre'],
        )
        async def torre_callback(message):
            """
            Instruções e ajuda para Jogo Torre
            """
            await message_callback(message, ['tc', 'torre', message.chat.type])
            command = await message.reply(f"""Instruções: Cada jogador(a)(e) \
começa no térreo de uma torre de andares infinitos. Use o comando /andar ou \
/level para escolher entre {faces} portas. Cada porta pode ter uma escada que \
faz:\n\n\
50% de chance: descer um andar;\n\
33.3~% de chance: subir um andar;\n\
16.6~% de chance: um atalho com uma escada para subir um número aleatório de \
andares entre 1 e {faces}.\n\n\
Não tem como ganhar o jogo nem perder, não é possível descer além do térreo \
(andar 0). O jogo dura enquanto eu pagar a hospedagem do servidor.\n\
Para ver as estatísticas individuais, use o comando /aonde ou /where\n\
Para ver as estatísticas globais (ranking), espere este comando existir.\n\
Para apagar todas as estatísticas e remover os dados, espere este comando \
existir.\n\
Para doar dinheiro e ajudar a manter o jogo no ar (e provavelmente adicionar \
mais elementos de jogo), fale com o desenvolvedor.\n\
Versão do jogo: v{version} (commit {commit})""")
            await command_callback(command, ['tc', 'torre', message.chat.type])

        @dispatcher.message_handler(
            commands = ['roll', 'rolar'],
        )
        async def roll_callback(message):
            """
            Acrescenta uma rolagem de dados para este usuário no banco de 
            dados, e retorna o próximo nível.
            """
            await message_callback(message, ['tc', 'roll', message.chat.type])
            try:
                roll = dice(faces)
                if not await set_tc_roll(
                    dispatcher.bot.id,
                    message.from_id,
                    roll,
                ):
                    raise
                levels = [v[1] for v in await get_tc_levels(dispatcher.bot.id,
                    message.from_id)]
                level, new_roll = await mapa.get(
                    roll,
                    lambda x, y, z: (-1, 0),
                )(
                    dispatcher.bot.id,
                    message.from_id,
                    levels,
                )
                if new_roll > 0:
                    await message.reply(f"""Resultado: {str(roll)}! \
Segundo dado: {str(new_roll)}. Novo nível: {str(level)}.\nPara jogar de novo, \
clique em /rolar\nPara ver as estatísticas, clique em /aonde\nPara \
instruções, clique em {comando}""")
                else:
                    await message.reply(f"""Resultado: {str(roll)}. \
Novo nível: {str(level)}.\nPara jogar de novo, clique em /rolar\nPara ver as \
estatísticas, clique em /aonde\nPara instruções, clique em {comando}""")
            except Exception as exception:
                logger.exception(exception)
                await message.reply("""Problemas técnicos. Avise o \
desenvolvedor (se é que já não avisaram) e tente novamente mais tarde.""")
                await error_callback(
                    "Problema tentando rodar /roll",
                    message,
                    exception,
                    ['tc', 'roll', 'exception', message.chat.type],
                )

        @dispatcher.message_handler(
            commands = ['where', 'aonde'],
        )
        async def where_callback(message):
            """
            Exibe um gráfico com o histórico de níveis deste user_id
            """
            await message_callback(message, ['tc', 'where', message.chat.type])
            figure_buffer = BytesIO()
            try:
                levels = await get_tc_levels(dispatcher.bot.id,
                    message.from_id)
                pyplot.plot([v[1] for v in levels])
                ## Essas três linhas estão tentando forçar escala em inteiros
                # ~ level_ticks = zip(levels)
                pyplot.xticks([v[0] for v in levels])
                pyplot.yticks([v[1] for v in levels])
                pyplot.title(f"""nível a cada jogada de \
{message['from']['first_name']}""")
                pyplot.xlabel("número da jogada")
                pyplot.ylabel("andar da torre")
                pyplot.savefig(figure_buffer, format = "png")
                try:
                    await message.reply_photo(
                        figure_buffer.getbuffer(),
                        caption = f"""Para abrir a próxima porta, clique em \
/andar\nPara ver as estatísticas, clique em /aonde\nPara instruções, clique \
em {comando}""",
                    )
                except Exception as exception:
                    await erro_callback(
                        u"Error trying to send graphic",
                        message,
                        exception,
                        ['tc', 'where', 'exception'],
                    )
                    raise
            except Exception as exception:
                logger.exception(exception)
                await message.reply("""Problemas técnicos. Avise o \
desenvolvedor (se é que já não avisaram) e tente novamente mais tarde.""")
                await error_callback(
                    "Problema tentando rodar /where",
                    message,
                    exception,
                    ['tc', 'where', 'exception', message.chat.type],
                )
            finally:
                figure_buffer.close()

        @dispatcher.message_handler(
            filters.Text(equals = icones),
        )
        async def door_callback(message):
            """
            Acrescenta uma rolagem de dados caracterizada como porta ou 
            elevador para este usuário no banco de dados, e retorna o próximo 
            nível.
            """
            await message_callback(message, ['tc', 'door', message.chat.type])
            try:
                roll = dice(faces)
                if not await set_tc_roll(
                    dispatcher.bot.id,
                    message.from_id,
                    roll,
                ):
                    raise
                levels = [v[1] for v in await get_tc_levels(dispatcher.bot.id,
                    message.from_id)]
                level, new_roll = await mapa.get(
                    roll,
                    lambda x, y, z: (-1, 0),
                )(
                    dispatcher.bot.id,
                    message.from_id,
                    levels,
                )
                if new_roll > 0:
                    await message.reply(
                        u"\U0001f51d" + u"\U000023eb" + f""" Parabéns! Esta \
porta tem um atalho para subir {str(new_roll)} andares!\n\
Andar atual: {str(level)}.\n\
Para abrir a próxima porta, clique em /andar\n\
Para ver as estatísticas, clique em /aonde\n\
Para instruções, clique em {comando}""")
                elif level > levels[-1]:
                    await message.reply(
                        u"\U00002705" + u"\U00002b06" + f""" Esta porta tinha \
uma escada para subir para o próximo andar.\n\
Andar atual: {str(level)}.\n\
Para abrir a próxima porta, clique em /andar\n\
Para ver as estatísticas, clique em /aonde\n\
Para instruções, clique em {comando}""")
                else:
                    await message.reply(
                        u"\U0000274c" + u"\U00002b07" + f""" Esta porta tinha \
uma escada para descer para o andar anterior.\n\
Andar atual: {str(level)}.\n\
Para abrir a próxima porta, clique em /andar\n\
Para ver as estatísticas, clique em /aonde\n\
Para instruções, clique em {comando}""")
            except Exception as exception:
                logger.exception(exception)
                await message.reply("""Problemas técnicos. Avise o \
desenvolvedor (se é que já não avisaram) e tente novamente mais tarde.""")
                await error_callback(
                    "Problema tentando rodar /door",
                    message,
                    exception,
                    ['tc', 'door', 'exception', message.chat.type],
                )

        @dispatcher.message_handler(
            commands = ['andar', 'level'],
        )
        async def andar_callback(message):
            """
            Menu com escolhas como alternativa a rolar dados
            """
            await message_callback(message, ['tc', 'level', message.chat.type])
            try:
                ## Para faces = 6, escolhas = [1,2,3,4,5,6]
                # ~ escolhas = list(range(1, faces + 1))
                ## Ordem pseudo aleatória a cada geração do menu
                # ~ numpy.random.default_rng().shuffle(escolhas)
                # ~ portas = zip(escolhas, icones[:len(escolhas)])
                menu = ReplyKeyboardMarkup()
                menu.row(*[KeyboardButton(icone) for icone in icones[:faces]])
                await message.reply(f"""Neste andar há \
{faces} portas, cada uma com um símbolo. Atrás de cada uma há uma escada que \
pode subir ou descer. Escolha o símbolo de uma porta para entrar""",
                    reply_markup = menu)
            except Exception as exception:
                logger.exception(exception)
                await message.reply("""Problemas técnicos. Avise o \
desenvolvedor (se é que já não avisaram) e tente novamente mais tarde.""")
                await error_callback(
                    "Problema tentando rodar /level",
                    message,
                    exception,
                    ['tc', 'level', 'exception', message.chat.type],
                )

    except Exception as exception:
        logger.exception(exception)
        raise
