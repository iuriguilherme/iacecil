"""
Plugin tc para ia.cecil: tower climbing game

ia.cecil

Copyleft 2016-2022 Iuri Guilherme <https://iuri.neocities.org/>

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

import numpy
import random
import time
from aiogram import (
    Dispatcher,
    filters,
)
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from io import BytesIO
from matplotlib import pyplot
from serpapi import GoogleSearch
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
    get_tc_prizes,
    set_tc_level,
    set_tc_prize,
    set_tc_roll,
)
from .mate_matica import dice

## Valores padrão
comando: str = 'torre'
faces: int = 9
## Mensagem motivacional a cada tantos andares
premio: int =  30
## Chance de voltar pro início (1.0 é 100%)
azar: float = 0.003
## Ajuda
help_icon: str = u"\U00002753"
## Estatísticas
stats_user: str = u"\U0001f4c8"
icones: list = [
    u"\U00002764", # vermelho
    u"\U0001f9e1", # laranja
    u"\U0001f49b", # amarelo
    u"\U0001f49a", # verde
    u"\U0001f499", # azul
    u"\U0001f49c", # roxo
    u"\U0001f5a4", # preto
    u"\U0001f90d", # branco
    u"\U0001f90e", # marrom
]

async def info() -> str:
    """Texto padrão para todos comandos de instruções e ajuda"""
    return f"""Instruções: Cada jogador(a)(e) começa no térreo de uma torre \
de andares infinitos. Use o comando /{comando} para abrir o teclado e \
escolher entre {faces} portas. Cada porta pode ter uma escada que faz uma das \
seguintes ações:\n\n\
Descer um andar (55.55~% de chance);\n\
Subir um andar (33.33~% de chance);\n\
Um atalho com uma escada para subir um número aleatório de andares entre 1 e \
{faces} (11.11~% de chance);\n\
Um buraco para voltar ao térreo (0.3% de chance).\n\n\
A cada {premio} andares, uma supresa!\n\n\
Não tem como ganhar o jogo nem perder, não é possível descer além do térreo \
(andar 0). O jogo dura enquanto eu pagar a hospedagem do servidor.\n\
Para ver as estatísticas individuais, use o ícone do teclado {stats_user}.\n\
Para ver as estatísticas globais (ranking), espere este comando existir.\n\
Para apagar todas as estatísticas e remover os dados, espere este comando \
existir.\n\
Para doar dinheiro e ajudar a manter o jogo no ar (e provavelmente adicionar \
mais elementos de jogo), fale com o desenvolvedor através do comando \
/feedback ou use o comando /donate\n\
Versão do jogo: v{version} (commit {commit})"""

async def prize(dispatcher: Dispatcher, message: Message, level: int,
    levels: list[int]) -> None:
    """
    Envia uma frase motivacional oriunda de busca de imagem no mecanismo de
    busca da Google
    """
    ## Eu sei que a pessoa passou por um nível múltiplo de 60 se o
    ## módulo (resto da divisão) de algum nível para todo nível
    ## entre o último nível e o nível atual for igual a zero.
    ## Caso especial: 0 dividido por 60 tem resto 0.
    if 0 in [
        lvl % premio \
        for lvl in range(levels[-1], level) \
        if lvl > 0
    ]:
        prizes: set = await get_tc_prizes(dispatcher.bot.id)
        last_prize: int = 1
        try:
            last_prize = sorted(prizes)[-1]
        except IndexError:
            ## FIXME: Só acontece uma vez quando o banco de dados é iniciado,
            ## Talvez iniciar com um valor 0 que nem os níveis?
            pass
        offset: int = 0
        ## O serpapi retorna 100 imagens a cada página, o problema
        ## aqui é pegar o índice da última imagem utilizada e
        ## descobrir em que página está. Para search['ijn'] = 0,
        ## imagens de 1 a 100. Para search['ijn'] = 1, imagens de
        ## 101 a 200, e assim por diante. Então ijn deve ser igual
        ## a offset - 1 para todo e qualquer índice tal que
        ## offset * 100 / índice < 1.
        ## 
        ## Medo de while (True):
        # ~ timeout: float = time.time() + 30
        # ~ while time.time() < timeout:
        ## 
        ## Rá! Divisão por zero
        while (offset * 100) / max(1, last_prize) < 1.0:
            offset += 1
        search: object = GoogleSearch({
            "api_key": dispatcher.config.serpapi['api_key'],
            "engine": "google",
            "q": "frase motivacional",
            "location": "Brazil",
            "google_domain": "google.com.br",
            "gl": "br",
            "hl": "pt-br",
            "safe": "active",
            "tbm": "isch",
            "ijn": str(offset - 1),
        })
        results: dict = search.get_dict()
        ## Exemplo de resultado:
        # ~ "images_results": [
            # ~ {
                # ~ "position": 1,
                # ~ "original": "example.jpg",
                # ~ "source": "example.com",
                # ~ "title": "Imagem",
                # ~ "link": "http://example.com/example",
                # ~ "thumbnail": "url.jpg",
            # ~ },
        # ~ ]
        ## Então o link para a próxima imagem é:
        image_url, image_position = [
            (i['original'], i['position']) \
            for i in search.get_dict()['images_results'] \
            if i['position'] == last_prize + 1
        ][0]
        await command_callback(
            await message.reply_photo(
                photo = image_url,
                caption = u"\U0001f3c6" + u"\U0001f973" + f""" \
Parabéns! A cada {str(premio)} níveis, uma frase motivacional. \
Continue subindo!\n\
Andar atual: {level}.\n\
Para abrir a próxima porta, clique em /{comando} ou num dos símbolos do \
teclado: {' '.join(icones[:faces])}.\n\
Para ver as estatísticas, clique no {stats_user}.\n\
Para instruções, clique no {help_icon}.""",
            ),
            ['tc', 'prize', message.chat.type],
        )
        ## Armazena imagens que já foram utilizadas
        await set_tc_prize(dispatcher.bot.id, image_position)

async def level_zero(dispatcher: Dispatcher, message: Message,
    levels: list[int]) -> None:
    level: int = 0
    await set_tc_level(dispatcher.bot.id, message.from_id, level)
    await message.reply(u"\U0001f629" + u"\U000023ec" + f""" Puta que pariu! \
Esta porta tinha um buraco, voltando pro começo!\n\
Andar atual: {level}.\n\
Para abrir a próxima porta, clique em /{comando} ou num dos símbolos do \
teclado: {' '.join(icones[:faces])}.\n\
Para ver as estatísticas, clique no {stats_user}.\n\
Para instruções, clique no {help_icon}.""")

async def level_down(dispatcher: Dispatcher, message: Message,
    levels: list[int]) -> None:
    """Manda o jogador um andar abaixo"""
    ## Não pode descer do térreo
    level: int = max(0, levels[-1] - 1)
    await set_tc_level(dispatcher.bot.id, message.from_id, level)
    await message.reply(u"\U0000274c" + u"\U00002b07" + f""" Esta porta tinha \
uma escada para descer para o andar anterior.\n\
Andar atual: {level}.\n\
Para abrir a próxima porta, clique em /{comando} ou num dos símbolos do \
teclado: {' '.join(icones[:faces])}.\n\
Para ver as estatísticas, clique no {stats_user}.\n\
Para instruções, clique no {help_icon}.""")

async def level_up(dispatcher: Dispatcher, message: Message,
    levels: list[int]) -> None:
    """Manda o jogador um andar acima"""
    level: int = levels[-1] + 1
    await set_tc_level(dispatcher.bot.id, message.from_id, level)
    await message.reply(u"\U00002705" + u"\U00002b06" + f""" Esta porta tinha \
uma escada para subir para o próximo andar.\n\
Andar atual: {level}.\n\
Para abrir a próxima porta, clique em /{comando} ou num dos símbolos do \
teclado: {' '.join(icones[:faces])}.\n\
Para ver as estatísticas, clique no {stats_user}.\n\
Para instruções, clique no {help_icon}.""")
    await prize(dispatcher, message, level, levels)

async def levels_up(dispatcher: Dispatcher, message: Message,
    levels: list[int]) -> None:
    """
    Rola mais um dado e manda o jogador tantos andares pra cima quanto for o 
    valor do segundo dado
    """
    roll: int = dice(faces)
    level: int = levels[-1] + roll
    await set_tc_level(dispatcher.bot.id, message.from_id, level)
    await message.reply(u"\U0001f51d" + u"\U000023eb" + f""" Parabéns! Esta \
porta tem um atalho para subir {roll} andares!\n\
Andar atual: {level}.\n\
Para abrir a próxima porta, clique em /{comando} ou num dos símbolos do \
teclado: {' '.join(icones[:faces])}.\n\
Para ver as estatísticas, clique no {stats_user}.\n\
Para instruções, clique no {help_icon}.""")
    await prize(dispatcher, message, level, levels)

mapa = {
    0: level_zero,
    1: level_down,
    2: level_down,
    3: level_down,
    4: level_down,
    5: level_down,
    6: level_up,
    7: level_up,
    8: level_up,
    9: levels_up,
}

async def add_handlers(dispatcher: Dispatcher) -> None:
    """
    Registra handlers em um Aiogram Dispatcher caso este plugin esteja
    habilitado.
    """
    try:
        @dispatcher.message_handler(
            filters.Text(equals = [u"\U00002753"]),
        )
        async def torre_callback(message: Message) -> None:
            """
            Instruções e ajuda para Jogo Torre
            """
            await message_callback(message, ['tc', 'torre', message.chat.type])
            await message.reply(await info())

        @dispatcher.message_handler(
            filters.Text(equals = [u"\U0001f4c8"]),
        )
        async def where_callback(message: Message) -> None:
            """
            Exibe um gráfico com o histórico de níveis deste user_id
            """
            await message_callback(message, ['tc', 'where', message.chat.type])
            try:
                figure_buffer: BytesIO = BytesIO()
                levels: list = await get_tc_levels(dispatcher.bot.id,
                    message.from_id)
                pyplot.plot([v[1] for v in levels])
                ## Essas três linhas estão tentando forçar escala em inteiros
                # ~ level_ticks = zip(levels)
                # ~ pyplot.xticks([v[0] for v in levels])
                # ~ pyplot.yticks([v[1] for v in levels])
                pyplot.title(f"""andar da torre a cada jogada de \
{message['from']['first_name']}""")
                pyplot.xlabel("número da jogada")
                pyplot.ylabel("andar da torre")
                pyplot.savefig(figure_buffer, format = "png")
                try:
                    await message.reply_photo(
                        figure_buffer.getbuffer(),
                        caption = f"""Jogadas: {len(levels)}, andar atual: \
{str([v[1] for v in levels][-1])}\n\
Para abrir a próxima porta, clique em /{comando} ou num dos símbolos do \
teclado: {' '.join(icones[:faces])}.\n\
Para ver as estatísticas novamente, clique no {stats_user}.\n\
Para instruções, clique no {help_icon}.""",
                    )
                except Exception as exception:
                    await erro_callback(
                        u"Error trying to send graphic",
                        message,
                        exception,
                        ['tc', 'where', 'exception'],
                    )
                    raise
                finally:
                    figure_buffer.close()
                    # ~ pyplot.figure().clear()
                    # ~ pyplot.cla()
                    pyplot.clf()
                    # ~ pyplot.close()
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

        @dispatcher.message_handler(
            filters.Text(equals = icones),
        )
        async def door_callback(message: Message) -> None:
            """
            Acrescenta uma rolagem de dados caracterizada como porta ou 
            elevador para este usuário no banco de dados, e retorna o próximo 
            nível.
            """
            await message_callback(message, ['tc', 'door', message.chat.type])
            try:
                roll: int = dice(faces)
                ## Chance de voltar pro início
                if numpy.random.random() < azar:
                    roll = 0
                if not await set_tc_roll(
                    dispatcher.bot.id,
                    message.from_id,
                    roll,
                ):
                    raise
                await mapa.get(roll, level_zero)(dispatcher, message,
                    [v[1] for v in await get_tc_levels(dispatcher.bot.id,
                    message.from_id)]
                )
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
            commands = [comando],
        )
        async def andar_callback(message: Message) -> None:
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
                level: int = [v[1] for v in await get_tc_levels(
                    dispatcher.bot.id, message.from_id)][-1]
                menu = ReplyKeyboardMarkup(
                    resize_keyboard = True,
                    # ~ one_time_keyboard = True,
                    selective = True,
                )
                menu.row(
                    *[KeyboardButton(icone) for icone in icones[:faces]],
                    KeyboardButton(stats_user),
                    KeyboardButton(help_icon),
                )
                await message.reply(f"""No andar {str(level)} da torre há \
{faces} portas, cada uma com um símbolo: {' '.join(icones[:faces])}.\n\
Atrás de cada uma dessas portas há uma escada que pode subir ou descer.\n\
Escolha no teclado o símbolo de uma porta para entrar.\n\
Clique em {stats_user} para ver as estatísticas, ou em {help_icon} para ver \
as instruções.""",
                    reply_markup = menu,
                )
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

        @dispatcher.message_handler(
            commands = ["start", "info", "help"],
        )
        async def start_callback(message: Message) -> None:
            """
            /start handler
            """
            await message_callback(message, ['tc', 'start', message.chat.type])
            await command_callback(await message.reply(await info()),
                ['tc', 'start', message.chat.type])
            await andar_callback(message)
    except Exception as e:
        logger.exception(e)
        raise
