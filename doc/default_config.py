# vim:fileencoding=utf-8
#
#  ia.cecil
#  
#  Copyleft 2012-2022 Iuri Guilherme <https://iuri.neocities.org/>
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
##
## PT: Copiar este arquivo para instance/config.py e editar lá
##
## EN: Copy this file to instance/config.py and edit it there

from pydantic import BaseSettings

class Config(BaseSettings):
    
    ### Configuração padrão para todos bots:
    ### Os bots definidos posteriormente podem herdar as configurações 
    ### padrão, ou uma parte das configurações conforme a necessidade.
    defaults: dict = {
        ### Common data pertinent to all bots
        'info': {
            'website': "https://matehackers.org",
            'repository': "https://github.com/iuriguilherme/iacecil",
            'group': "https://t.me/joinchat/CwFUFkf-dKW34FPBjEJs9Q",
            'channel': "@matebotnews",
            'admin': "@desobedientecivil",
            'dev': "@desobedientecivil",
            ## Plugin donate - doações
            'donate': {
                'btc': "1AG2SX3n9iFQiZExiyS3M5qCuZT5GhArn",
                'crypto': {
                    'BCH': '1HFG6ici2SGU61hPFFtUsPVGMkdiimBPDL',
                    'BTC': '1MQJSCb6VopUeYrrsQaFVwmyFzs1hffcD2',
                    'DOGE': 'DAeuBKyt6gSnD5rT5eBtjvXqdGvFWVkh9D',
                    'ETH': '0x083652085dc46ab2d6146fbb329db0cde48eea81',
                    'FLO': 'F87gjmfeF9nWh1suB5X2TZQNN6FaQyWzxp',
                    'LTC': 'LY8w2WBRogttTJbLfusrJogi2tp6rKrPc3',
                    'PIVX': 'D9bUN6xhDTRUZYCT54yLw6L2F1QaMJ3oTC',
                    'TRX': 'TTCooALnSqmFcK3q56WMnGmbYhaXR6Zh5e',
                }, # crypto
            }, # donate
            ## Plugin tropixel - colar os links aqui no lugar de 
            ## "Não sei !"
            'tropixel': {
                'site': "Não sei!",
                'boteco': "Não sei!",
            },
            ## Plugin personalidades
            'personalidade': 'default',
            ## Plugin cryptoforex
            'coinmarketcap_token': '00000000-0000-0000-0000-000000000000',
            ## Plugin TecidoTextoPalavra
            'tecido': {
                'host': '127.0.0.1',
                'port': 3000,
            },
            ## Plugin web3_wrapper
            'web3': {
                'binance': {
                    'bsc_mainnet': 'https://bsc-dataseed1.binance.org:443',
                    'bsc_testnet': 'https://data-seed-prebsc-1-s1.binance.org:8545',
                }, # binance
                'infura': {
                    ## https://infura.io/register
                    'eth_mainnet': 'https://mainnet.infura.io/v3/1234567890',
                    'eth2_mainnet': 'https://1234567890:1234567890@eth2-beacon-mainnet.infura.io',
                    'filecoin': 'https://1234567890:1234567890@filecoin.infura.io',
                }, # infura
            }, # web3
            ## Plugin calendar
            'jobs': [],
            'timezone': 'America/Sao_Paulo',
            ### Níveis de permissão (inspirados no Brave New World):
            ###
            ### Os usuários e grupos cujos ids estão na lista 
            ### bot.config['telegram']['users']['alpha'] só vão ter 
            ### acesso aos comandos que fazem parte dos plugins da lista
            ### bot.config['info']['plugins']['alpha']. Assim como a 
            ### lista bot.config['telegram']['users']['beta'] é relativa
            ### à lista bot.config['info']['plugins']['beta'], e assim 
            ### por diante. Esta é a única regra.
            ###
            ### Sinta-se livre para liberar o acesso a todos os comandos
            ### para qualquer pessoa ou grupo, ou para criar ainda mais 
            ### níveis de controle de acesso.
            ###
            ### Se isto não estiver claro, veja os exemplos no arquivo 
            ### README.md ou peça ajuda no grupo: 
            ### https://t.me/joinchat/CwFUFkf-dKW34FPBjEJs9Q
            ###
            ### A lista bot.config['info']['plugins']['omega'] é 
            ### especial e serve para dar acesso a comandos para toda e 
            ### qualquer pessoa ou grupo.
            ###
            'plugins': {
                ## New way to handle plugins since v0.1.17:
                ##
                ## Override bot.config['info']['plugins']['enable'] to
                ## including only the desired plugins and disabling
                ## everything else.
                ##
                ## Override bot.config['info']['plugins']['disable'] to
                ## exclude plugins from activation, even if they're
                ## listed on bot.config['info']['plugins']['enable'].
                ##
                ## You can't force activate plugins on the 'enable'
                ## list, have to make sure they're not present in
                ## 'disable'.
                ##
                ## The old 'alpha' to 'omega' lists are still not
                ## implemented, so they don't do nothing right now.
                ##
                ## The 'all' key is left in the default_config.py for
                ## reference and may not be up to date. Check the
                ## plugins folder.
                ##
                ## NOTICE: Make sure you organize the list in the order
                ## that the plugins should be added because aiogram's
                ## dispatcher.register_handler uses the order in which
                ## handlers are added. First match will trigger and
                ## ignore all the next handlers.
                ##
                'all': [
                    'default', 'admin', 'archive', 'cryptoforex',
                    'donate', 'echo', 'feedback', 'garimpo', 'greatful',
                    'hashes', 'mate_matica', 'natural', 'portaria',
                    'qr', 'storify', 'totalvoice', 'tropixel', 'tts',
                    'web3_wrapper', 'welcome', 'ytdl',
                ], # all
                ## Plugins enabled by default
                'enable': ['default', 'admin'],
                'disable': [],
                ## Lista de plugins disponíveis somente para 
                ## bot.config['telegram']['users']['alpha']
                ## Sugestão de uso: pessoa que criou o bot, etc.
                'alpha': ["admin",],
                ## Lista de plugins disponíveis somente para 
                ## bot.config['telegram']['users']['beta']
                ## Sugestão de uso: administradora(e)s, moderadora(e)s, 
                ## etc.
                'beta': ["admin",],
                ## Lista de plugins disponíveis somente para 
                ## bot.config['telegram']['users']['gamma']
                ## Sugestão de uso: grupos e canais onde quem administra
                ## tem controle
                'gamma': ["donate",],
                ## Lista de plugins disponíveis somente para 
                ## bot.config['telegram']['users']['delta']
                ## Sugestão de uso: grupos e canais onde quem administra
                ## acompanha mas não controla
                'delta': ["personalidades", "feedback", "welcome",],
                ## Lista de plugins disponíveis somente para 
                ## bot.config['telegram']['users']['epsilon']
                ## Sugestão de uso: grupos, canais e usuários que usam o 
                ## bot regularmente
                'epsilon': ["archive", "hashes", "mate_matica", "qr",
                    "ytdl",
                ],
                ## Lista de plugins ativos para todo mundo
                'omega': ["telegram",],
            }, # plugins
        }, # info
        ### Flask / Quart configuration
        'quart': {
        }, # quart
        ### Configuration specific to Telegram Bot API
        'telegram': {
            'token': None,
            'webhook': {
                'host': 'https://127.0.0.1',
                'path': '/telegram',
                'webapp': 'https://127.0.0.1/telegram',
                'port': 8443,
            }, # webhook
            ## Plugin portaria
            'unwanted': [
                'HV Cursos',
                'MateBot (dev)',
            ], # unwanted
            'users': {
                ### telegram_id de usuária(o)s ou grupos
                ### Envie /start para descobrir o próprio id
                'alpha': [1,-1,],
                'beta': [],
                'gamma': [-481703172,],
                'delta': [-1001233916997,],
                'epsilon': [777000,-1001207858341,],
                ## Plugin Welcome
                'pegadinha': [-1001233916997,],
                ## Plugin Tropixel
                'tropixel': [-1001233916997,],
                ## Plugin garimpo: allowed groups for garimpa_tudo
                'garimpo': [-1001207858341],
                ### Não tem 'omega' porque 'omega' é qualquer outro id
                ### Usuários e grupos especiais (que são referenciados 
                ### pelo nome da chave)
                'special': {
                    ## Conta de serviço do telegram
                    'service': 777000,
                    ## Grupo público para desenvolvedora(e)s e 
                    ## usuária(o)s
                    ## https://t.me/joinchat/CwFUFkf-dKW34FPBjEJs9Q
                    'pub': -1001207858341, 
                    ## Grupo para onde vão mensagens de informação
                    ## https://t.me/joinchat/CwFUFhy2NQRi_9Cc60v_aA
                    'info': -481703172,
                    ## Grupo para onde são logados os erros / exceções
                    ## https://t.me/joinchat/CwFUFhy2NQRi_9Cc60v_aA
                    'debug': -481703172,
                    ## Grupo para onde vão as mensagens do comando 
                    ## /feedback
                    ## https://t.me/joinchat/CwFUFhy2NQRi_9Cc60v_aA
                    'feedback': -481703172,
                    ## Grupo para testar bots
                    ## https://t.me/joinchat/CwFUFhbgApLHBMLoNnkiRg
                    'test': -1001233916997,
                    ## Plugin Garimpo
                    'garimpo': -1001233916997,
                    ## Telegram's way to anonymize channel owner
                    'groupanonymousbot': 1087968824,
                    ## When user sends message as a channel
                    'Channel_Bot': 136817688,
                }, # special
            }, # users
        }, # telegram
        ### Discord.py configuration
        'discord':{
            'token': None,
        }, # discord
        'furhat': {
            # Robot identifier
            'bot': 'f1',
            # Network address of Furhat Robot
            'address': '127.0.0.1',
            # Default Amazon Polly Language
            'language': 'pt-BR',
            # Default Amazon Polly Voice
            'voice': 'Camila',
            # Default FaceCore Mask
            'mask': 'adult',
            # Default FaceCore Character
            'character': 'Titan',
            # Default Led Color
            'led': {'gren': 0, 'red': 0, 'blue': 0},
            # Default attend position
            'attend': {'x': 0, 'y': 0, 'z': 0},
            # Default URL for voice files storage
            'voice_url': 'https://denise.matehackers.org/audio/',
            # STT recognizer credentials
            'recognizer': {
                # https://cloud.google.com/speech/docs/getting-started
                'google': {
                    "type": None,
                    "project_id": None,
                    "private_key_id": None,
                    "private_key": None,
                    "client_email": None,
                    "client_id": None,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_x509_cert_url": None,
                }, # google
                # https://azure.microsoft.com/en-us/services/cognitive-services/speech-to-text/
                'microsoft': {}, # microsoft
            }, # recognizer
            # TTS synthesizer credentials
            'synthesizer': {
                # https://aws.amazon.com/pt/polly/
                'amazon': {
                    'secret': None,
                    'key': None,
                    'engine': 'neural',
                }, # amazon
                # https://www.acapela-group.com/solutions/acapela-cloud/
                'acapela': {}, # acapela
            }, # synthesizer
        }, # furhat
    } # defaults

    quart: dict = {
        ## Copy from default configuration
        defaults['quart'].copy()
    } # quart

    bots: dict = {
        ### O nome da chave (por exemplo 'iacecil') é o nome do bot 
        ### como parâmetro ao invocar o script. Isto permite usar 
        ### múltiplos bots na mesma thread, (quase) todos comandos 
        ### assíncronos.
        ### As chaves 'production', 'testing' e 'development' podem ser 
        ### utilizadas juntamente com as variáveis de ambiente do QUART.
        'iacecil': dict(
            ## This copies all default configuration
            defaults.copy(),
            ## Now we'll override the ones we need to change
            info = dict(
                ## Have to copy all sub dicts
                defaults['info'].copy(),
                personalidade = 'iacecil',
                plugins = dict(
                    defaults['info']['plugins'].copy(),
                    enable = defaults['info']['plugins']['enable'] + [
                        'archive', 'donate', 'hashes', 'mate_matica',
                        'portaria', 'qr', 'welcome',
                    ], # enable
                    disable = ['admin', 'echo'],
                ), # plugins
            ), # info
            telegram = dict(
                defaults['telegram'].copy(),
                ## Obtenha um token com @BotFather no Telegram
                token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            ), # telegram
        ), # iacecilbot        
        'production': dict(
            defaults.copy(),
            telegram = dict(
                defaults['telegram'].copy(),
                token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            ), # telegram
        ), # production
        'testing': {
            defaults.copy(),
            telegram = dict(
                defaults['telegram'].copy(),
                token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            ), # telegram
        }, # testing
        'development': dict(
            defaults.copy(),
            info = dict(
                defaults['info'].copy(),
                ## Changing personalidade
                personalidade = 'matebot',
                plugins = dict(
                    defaults['info']['plugins'].copy(),
                    enable = defaults['info']['plugins']['enable'] + [
                        'archive', 'donate', 'echo', 'feedback',
                        'garimpo', 'hashes', 'mate_matica', 'natural',
                        'portaria', 'qr', 'storify', 'tropixel', 'tts',
                        'welcome', 'ytdl',
                    ], # enable
                ), # plugins
                jobs = defaults['info']['jobs'] + [
                    {
                        'name': 'test_now',
                        'args': [],
                        'kwargs': {},
                    },
                ], # jobs
            ), # info
            telegram = dict(
                defaults['telegram'].copy(),
                token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
                ## Exemplo (ruim) para herdar configurações padrão 
                ## alterando algumas
                users = dict(
                    defaults['telegram']['users'].copy(),
                    special = {
                        'debug': -481703172,
                        'feedback': -481703172,
                        'info': -481703172,
                    }, # special
                ), # users
            ), # telegram
        ), # development
        ## The @cryptoforexbot
        'cryptoforexbot': dict(
            defaults.copy(),
            info = dict(
                defaults['info'].copy(),
                personalidade = 'cryptoforex',
                plugins = dict(
                    defaults['info']['plugins'].copy(),
                    ## Don't copy default enabled plugins, override it
                    enable = [
                        'cryptoforex', 'donate', 'feedback', 'hashes',
                        'mate_matica', 'qr', 'tts', 'web3_wrapper',
                    ], # enable
                    disable = ['admin', 'echo', 'portaria', 'welcome'],
                ), # plugins
            ), # info
            telegram = dict(
                defaults['telegram'].copy(),
                token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            ), # telegram
        ), # cryptoforexbot
        ## Exemplo de bot de discord (usar token do discord no lugar da
        ## token que seria do telegram)
        'discord_bot': dict(
            defaults.copy(),
            discord = dict(
                defaults['discord'].copy(),
                'token': "123456789ABCDEFghijklmno.123456.123456789ABCDEFghijklmnopqr",
            ), # discord
        ), # discord_bot
        ## Example of furhat only bot, altering configs useful to that
        ## Remember multiple bots can use a single furhat robot's
        ## remote api. It'll change the face and led according to the
        ## bot configured here.
        ## To use multiple furhat robots, each one should use it's own
        ## defaults['furhat']['address'].
        'furhat_bot': dict(
            defaults.copy(),
            info = dict(
                defaults['info'].copy(),
                personalidade = 'matebot',
            ), # info
            furhat = dict(
                defaults['furhat'].copy(),
                name = 'f2'
                character = 'Fedora',
                voice = 'Salli',
                language = 'en-US',
                led = {'red': 6, 'green': 30, 'blue': 240},
            ), # furhat
        ), # furhat_bot
    } # bots
