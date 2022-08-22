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
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from matplotlib import pyplot
from io import BytesIO
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

async def level_down(dispatcher.bot.id: str, user_id: str, levels: list) -> int:
    level = max(0, levels[-1] - 1)
    await set_tc_level(dispatcher.bot.id, user_id, level)
    return (level, 0)

async def level_up(dispatcher.bot.id: str, user_id: str, levels: list) -> int:
    level = levels[-1] + 1
    await set_tc_level(dispatcher.bot.id, user_id, level)
    return (level, 0)

async def levels_up(dispatcher.bot.id: str, user_id: str, levels: list) -> int:
    roll = dice(faces)
    level = levels[-1] + roll
    await set_tc_level(dispatcher.bot.id, user_id, level)
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
            command = await message.reply(f"""Instruções: Cada jogador começa \
no térreo de uma torre de andares infinitos. Use o comando /rolar ou /roll \
para rolar um dado de {faces} faces. Caso o resultado seja:\n\n\
1, 2 ou 3: Desça um andar;\n\
4 ou 5: Suba um andar;\n\
6: Role o dado novamente e suba tantos andares quanto o valor do segundo \
dado.\n\n\
Não tem como ganhar o jogo nem perder, não é possível descer além do térreo \
(andar 0). O jogo dura enquanto eu pagar a hospedagem do servidor.\n\
Para ver as estatísticas individuais, use o comando /aonde ou /where\n\
Para ver as estatísticas globais (ranking), espere este comando existir.\n\
Para apagar todas as estatísticas, espere este comando existir.\n\
Para doar dinheiro e ajudar a manter o jogo no ar (e provavelmente adicionar \
mais elementos de jogo), fale com o desenvolvedor.\n\
Quem quiser começar no andar três mil pode propor relações mutuamente \
benéficas envolvendo favores sexuais para o desenvolvedor.""")
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
                rolled = await set_tc_roll(dispatcher.bot.id, message.from_id, roll)
                levels = [v[1] for v in await get_tc_levels(dispatcher.bot.id,
                    message.from_id)]
                level, new_roll = await mapa[roll](dispatcher.bot.id, message.from_id,
                    levels)
                if new_roll > 0:
                    command = await message.reply(f"""Resultado: {str(roll)}! \
Segundo dado: {str(new_roll)}. Novo nível: {str(level)}.\nPara jogar de novo, \
clique em /rolar\nPara ver as estatísticas, clique em /aonde\nPara \
instruções, clique em {comando}""")
                else:
                    command = await message.reply(f"""Resultado: {str(roll)}. \
Novo nível: {str(level)}.\nPara jogar de novo, clique em /rolar\nPara ver as \
estatísticas, clique em /aonde\nPara instruções, clique em {comando}""")
            except Exception as exception:
                logger.exception(exception)
                command = await message.reply("""Problemas técnicos. Avise o \
desenvolvedor (se é que já não avisaram) e tente novamente mais tarde.""")
            await command_callback(command, ['tc', 'roll', message.chat.type])

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
                levels = [v[1] for v in await get_tc_levels(dispatcher.bot.id,
                    message.from_id)]
                pyplot.plot(levels)
                pyplot.title(f"""nível a cada jogada de \
{message['from']['first_name']}""")
                pyplot.xlabel("número da jogada")
                pyplot.ylabel("andar da torre")
                pyplot.xaxis.get_major_locator().set_params(integer=True)
                pyplot.yaxis.get_major_locator().set_params(integer=True)
                pyplot.savefig(figure_buffer, format = "png")
                try:
                    command = await message.reply_photo(
                        figure_buffer.getbuffer(),
                        caption = f"""Para jogar de novo, clique em /rolar\n\
Para ver as estatísticas, clique em /aonde\nPara instruções, clique em \
{comando}""",
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
                command = await message.reply("""Problemas técnicos. Avise o \
desenvolvedor (se é que já não avisaram) e tente novamente mais tarde.""")
            finally:
                figure_buffer.close()
            await command_callback(command, ['tc', 'where', message.chat.type])
    except Exception as exception:
        logger.exception(exception)
        raise
