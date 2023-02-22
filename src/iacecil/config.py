"""
Default configuration for ia.cecil

ia.cecil

Copyleft 2012-2023 Iuri Guilherme <https://iuri.neocities.org/>

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

!!!!!!!!!!!!!!! ATENÇÃO !!!!!!!!!!!!!!!
Vós que vierdes editar este arquivo, perdei toda a esperança! O lugar 
apropriado para configurar o aplicativo é no arquivo .env
As diretivas de configuração que forem usadas lá serão carregadas por este 
arquivo aqui. Não há uma boa razão para alterar os valores padrão deste 
arquivo.
Veja o arquivo de referência example.env no diretório doc para aprender a 
criar um arquivo .env
Também é possível usar variáveis de ambiente do jeito clássico do sistema 
operacional, estas variáveis vão ser usadas preferencialmente e sobrescrever 
até mesmo o arquivo .env
!!!!!!!!!!!!!!! ATENÇÃO !!!!!!!!!!!!!!!

WARNING: Do not edit this file. Use the .env file or regular environment 
variables. The full explanation to such a request lies in the above portuguese 
notice, please translate it to your local language, thanks.

This is the old documentation for the ancient starting script:  

### Arguments explanation
### Usage: start.py log_level mode bots port host _reload canonical
### Defaults: start.py info quart iacecil 8000 127.0.0.1 True None
###
### log_level: Used in the logging module globally, this included 
### imported libraries where applicable;
###
### mode: One of the pre defined modes of operation in the main routine 
### at start.py. This is done because different mode of operation 
### require different settings. For example supporting long polling and 
### webhooks would require a huge rewrite everytime so it's easier to 
### set up such running environments in one single file. Also 
### development and production setups are not always a matter of 
### running quart on development mode, but this wrapper (start.py) 
### should take care of everything to make it simple to run easily in 
### whichever settings;
###
### bots: This would be an alias (or a comma separated list of aliases) 
### for bots already configured at instance/config.py. This allows for 
### selection of which bot tokens will be used simultaneously in an 
### environment where they should be selected before the script starts 
### such as all bots running in long polling mode.
###
### port: TCP port for uvicorn/quart binding;
###
### host: fqdn, ipv4 or localhost hostname for uvicorn/quart binding;
###
### _reload: uvicorn specific development option;
###
### canonical: (currently unused) gambiarra to make routes work in 
### subdirectories. Spoiler alert: it never worked;
###

### This file exists and it's expected to have dozens of lines because 
### this software has been historically been rewritten from scratch to 
### support / test / experiment with multiple technologies while not 
### breaking old versions of the running scripts. It is desirable to 
### add new controllers at iacecil/controllers and import them from 
### this file / command line calling than to refactor all code to force 
### the whole software to stick to one way of working. This versatility 
### feature comes from years of experience rewriting thousands of lines 
### of code, also inspired by plugin based similar software which in 
### itself probably has yet more decades of experience. So if you think 
### you have a better idea or feel an urge to "clean up" by removing 
### unused ancient code, fork the repository and have fun.
"""

import logging
logger = logging.getLogger(__name__)

try:
    import os
    import sys
    from importlib import import_module
    from datetime import tzinfo
    from pydantic import (
        BaseModel,
        BaseSettings,
        Field,
    )
    from pytz import timezone
    from pytz.tzinfo import DstTzInfo
    from secrets import token_hex
    from typing import (
        Dict,
        Type,
        Union,
    )
    ## Configuração baseada em instance (flask/quart)
    # ~ basedir = os.path.abspath(os.path.dirname(__file__))
    # ~ try:
        # ~ os.makedirs(os.path.join(basedir, 'instance'))
    # ~ except Exception as e:
        # ~ logger.debug("Caminho instance/ já existe")
        # ~ logger.exception(e)
    
    # ~ def get_default_bot(*args, **kwargs) -> dict:
        # ~ """Returns dictionary with default configuration"""
        # ~ try:
            # ~ return getattr(
                # ~ import_module(
                    # ~ 'instance.config',
                # ~ ),
                # ~ 'default_bot',
            # ~ )()
        # ~ except (ModuleNotFoundError, AttributeError) as e:
            # ~ logger.critical(f"""Default configuration files not found. Using \
# ~ fallback configuration instead.""")
            # ~ logger.exception(e)
            # ~ return getattr(
                # ~ import_module(
                    # ~ 'doc.config',
                # ~ ),
                # ~ 'default_bot',
            # ~ )()

    # ~ def get_bot(name: str, *args, **kwargs) -> dict:
        # ~ """Returns dictionary with configuration for bot with name"""
        # ~ try:
            # ~ return getattr(
                # ~ import_module(
                    # ~ '.bots.' + name,
                    # ~ 'instance',
                # ~ ),
                # ~ 'bot',
            # ~ )(get_default_bot())[0]
        # ~ except (ModuleNotFoundError, AttributeError) as e:
            # ~ logger.critical(f"""Configuration files for {name} not found. \
# ~ Using default configuration instead.""")
            # ~ logger.exception(e)
            # ~ return getattr(
                # ~ import_module(
                    # ~ 'doc.config',
                # ~ ),
                # ~ 'default_bot',
            # ~ )()
    
    class BotConfig(BaseSettings):
        """Configuration template class for each bot"""
        coinmarketcap: dict[str, str]
        discord: dict[str, str]
        donate: dict[str, str]
        furhat: dict[str, str]
        info: dict[str, str]
        openai: dict[str, str]
        jobs: list[str]
        personalidade: str
        plugins: dict[str, list]
        serpapi: dict[str, str]
        tecido: dict[str, Union[str, int]]
        telegram: dict[str, str]
        timezone: str
        tropixel: dict[str, str]
        web3: dict[str, str]
        # ~ tz_str: str
        # ~ timezone: Union[DstTzInfo, tzinfo, None]
        # ~ def set_tz(self):
            # ~ self.timezone = timezone(self.tz_str)

    class BaseConfig(BaseSettings):
        """
        Configuração padrão para ia.cecil
        Tudo o que deve ser alterado independemente do ambiente deveria estar 
        aqui.  
        Arquivos .env, config.ini, user.cfg, diretório instance/ e demais 
        configurações específicas do ambiente não devem estar aqui.  
        Somente configurações comuns para todas versões de ia.cecil devem 
        constar neste arquivo e mantidas sob versionamento.  
        Estes valores serão substituídos pelos valores do arquivo .env  
        Não edite os valores padrão deste arquivo
        Não edite os valores padrão deste arquivo
        Não edite os valores padrão deste arquivo
        Não edite os valores padrão deste arquivo
        Não edite os valores padrão deste arquivo
        Não edite os valores padrão deste arquivo
        """
        # ~ log_level: str = 'INFO'
        log_level: str = 'DEBUG'
        ## Uvicorn
        socket: Union[str, None] = 'uvicorn.sock'
        forwarded_allow_ips: str = '*'
        timeout_keep_alive: int = 0
        host: Union[str, None] = 'localhost'
        port: Union[int, None] = 8000
        ## FastAPI
        # ~ api: str = 'http://' + host + ':' + str(port) + '/api/'
        env: Union[str, None] = None
        debug: Union[bool, None] = None
        testing: Union[bool, None] = None
        # ~ oauthlib_insecure_transport: Union[bool, None] = None
        # ~ sqlalchemy_track_modifications: Union[bool, None] = None
        # ~ sqlalchemy_database_uri: Union[str, None] = None
        # ~ secret_key: Union[str, None] = None
        # ~ wtf_crsf_secret_key: Union[str, None] = None
        canonical: Union[str, None] = None
        log_messages: bool = True
        personas: list = ['default']
        add_startswith: Union[str, None] = None
        add_endswith: Union[str, None] = None
        text: Union[str, None] = None
        language_code: str = 'pt-BR'
        locale: str = 'pt_BR.UTF-8'
        quart: dict[str, str] = {}
        ## Furhat
        furhat: Union[dict, bool] = False
        ## ChatGPT
        openai: dict | None = None
        _reload: bool = False
        skip_intro: bool = True
        class Config:
            """Configuration for Pydantic"""
            case_sensitive: bool = False
            env_file: str = '.env'
    class ProductionConfig(BaseConfig):
        """Configuration for production staging"""
        class Config:
            env_prefix: str = "PROD_"
    class TestingConfig(BaseConfig):
        """Testing configuration"""
        class Config:
            env_prefix: str = "TEST_"
    class DevelopmentConfig(BaseConfig):
        """Development configuration"""
        class Config:
            env_prefix: str = "DEV_"

    class DefaultBotConfig(BaseSettings):
        """Default bot configuration"""
        ## All plugins: 'default', 'admin', 'archive', 'cryptoforex',
        ## 'donate', 'echo', 'feedback', 'garimpo', 'greatful',
        ## 'hashes', 'mate_matica', 'natural', 'portaria',
        ## 'qr', 'storify', 'totalvoice', 'tropixel', 'tts',
        ## 'welcome', 'ytdl'
        ## FIXME: Some plugins currently will not work if loaded after others,
        ## have to find out which is the correct order
        plugins: dict = {
            'enable': [
                'default',
                'admin',
            ], # enable
            'disable': [
                'archive',
                'cryptoforex',
                'donate',
                'feedback',
                'hashes',
                'mate_matica',
                'qr',
                'storify',
                'tropixel',
                'tts',
                'web3_wrapper',
                'ytdl',
                'natural',
                'welcome',
                'garimpo',
                'echo',
                'greatful',
                'portaria',
                'totalvoice',
            ], # disable
        }
        info: dict = {
            'website': "http://iuri.xyz/iacecil",
            'repository': "https://github.com/iuriguilherme/iacecil",
        }
        
        ## Plugin donate - doações
        donate: dict = {
            'BCH': '1HFG6ici2SGU61hPFFtUsPVGMkdiimBPDL',
            'BTC': '1MQJSCb6VopUeYrrsQaFVwmyFzs1hffcD2',
            'DOGE': 'DAeuBKyt6gSnD5rT5eBtjvXqdGvFWVkh9D',
            'ETH': '0x083652085dc46ab2d6146fbb329db0cde48eea81',
            'FLO': 'F87gjmfeF9nWh1suB5X2TZQNN6FaQyWzxp',
            'LTC': 'LY8w2WBRogttTJbLfusrJogi2tp6rKrPc3',
            'PIVX': 'D9bUN6xhDTRUZYCT54yLw6L2F1QaMJ3oTC',
            'TRX': 'TTCooALnSqmFcK3q56WMnGmbYhaXR6Zh5e',
        } # donate
        
        ## Plugin Tropixel
        tropixel: dict = {
            'site': "https://rede.tropixel.org/",
            'boteco': "https://meet.jit.si/tropixelbr",
        }
        ## Plugin personalidade
        ## List of working personalidades: 'iacecil', 'cryptoforex', 'default', 
        ## 'matebot', 'metarec', 'pave', 'pacume', 'pasoca'
        personalidade: str = 'default'
        
        ## Plugin cryptoforex
        coinmarketcap: dict = {
            'token': "12345678-90ab-cdef-1234-567890abcdef",
        } # coinmarketcap
        
        ## Plugin TextoTecidoPalavra
        tecido: dict = {
            'host': '127.0.0.1',
            'port': 3000,
        } # tecido
        
        ## Plugin web3_wrapper
        web3: dict = {
            'binance': {
                'bsc_mainnet': "https://bsc-dataseed1.binance.org:443",
                'bsc_testnet': """https://data-seed-prebsc-1-s1.binance.org:85\
45""",
            }, # binance
            'infura': {
                'eth_mainnet': """https://mainnet.infura.io/v3/0123456789abcde\
f0123456789abcdef""",
                'eth2_mainnet': """https://0123456789abcdef0123456789abcdef:01\
23456789abcdef0123456789abcdef@eth2-beacon-mainnet.infura.io""",
                'filecoin': """https://0123456789abcdef0123456789abcdef:012345\
6789abcdef0123456789abcdef@filecoin.infura.io""",
            }, # infura
        } # web3
        
        ## Plugin calendar
        jobs: list = []
        timezone: str = "Etc/UTC"
        
        ## Plugin tc
        serpapi: dict = {
            'api_key': "12345678-90ab-cdef-1234-567890abcdef",
        }
        
        quart: dict = {}
        telegram: dict = {
            'token': "",
            'info': {
                'group': "https://t.me/joinchat/CwFUFkf-dKW34FPBjEJs9Q",
                'channel': "@matebotnews",
                'admin': "@desobedientecivil",
                'dev': "@desobedientecivil",
            },
            'webhook': {
                'host': "https://iacecil.iuri.xyz/webhook/",
                'path': "/iacecil",
                'webapp': "https://iacecil.iuri.xyz/webhook/iacecil/",
                'port': 8443,
            }, # webhook
            ## Plugin portaria
            'unwanted': [
                "HV Cursos",
                "MateBot (test)",
            ], # unwanted
            'users': {
                'alpha': [
                    -1001233916997, # pub4 test
                ],
                'beta': [
                    -1001233916997, # pub4 test
                    -1001123697262, # MateBot News
                ],
                'gamma': [
                    -1001286967165, # pub1 G
                    -296878012, # pub2 C
                    -1001207858341, # pub3 M
                    -1001233916997, # pub4 test
                    -481703172, # pub5 test
                ],
                'delta': [
                ],
                'epsilon': [
                    777000, # services
                    -1001286967165, # pub1 G
                    -296878012, # pub2 C
                    -1001207858341, # pub3 M
                    -1001233916997, # pub4 test
                    -481703172, # pub5 test
                    -1001123697262, # MateBot News
                    # @mate_obot
                ], # epsilon
                'tropixel': [
                    -1001233916997, # pub4 test
                ], # tropixel
                'pegadinha': [
                    -1001233916997, # pub4 test
                ], # pegadinha
                'garimpo': [
                    -1001233916997, # pub4 test
                ],
                'special': {
                    'services': 777000,
                    'nouser': 1,
                    'nogroup': -1,
                    'debug': -1001233916997, # pub4 test
                    'feedback': -1001233916997, # pub4 test
                    'info': -1001233916997, # pub4 test
                    'test': -1001233916997, # pub4 test
                    'log_test': -1001233916997, # pub4 test
                    'garimpo': -1001233916997, # pub4 test
                }, # special
            }, # users
        } # telegram
        discord: dict = {
            'token': "",
        } # discord
        furhat: dict = {
            'bot': "f1",
            'address': "127.0.0.1",
            'voice': "Camila",
            'mask': "adult",
            'character': "Titan",
            'language': "pt-BR",
            'led': {'green': 0, 'red': 150, 'blue': 30},
            'attend': {'x': 0, 'y': 0, 'z': 0},
            'voice_url': "https://www.intriguing.com/mp/_sounds/hg/",
            'recognizer': {
                ## https://cloud.google.com/speech/docs/getting-started
                'google': {
                    "type": "service_account",
                    "project_id": "test_account",
                    "private_key_id": "1234567890abcdef",
                    "private_key": "privatekey",
                    "client_email": "example@example.com",
                    "client_id": "123456789",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": """https://www.googleapis.c\
om/oauth2/v1/certs""",
                    "client_x509_cert_url": """https://www.googleapis.com/robo\
t/v1/metadata/x509/example@example.com""",
                }, # google
                ## https://azure.microsoft.com/en-us/services/
                ## cognitive-services/speech-to-text/
                'microsoft': {}, # microsoft
            }, # recognizer
            'synthesizer': {
                ## https://aws.amazon.com/pt/polly/
                'amazon': {
                    'secret': "1234567890abcdef",
                    'key': "ABCDEF",
                    'engine': "neural",
                }, # amazon
                ## https://www.acapela-group.com/solutions/acapela-cloud/
                'acapela': {}, # acapela
            }, # synthesizer
            'extension': "wav",
            'output_format': "pcm",
        } # furhat
        openai: dict = {
            'api_key': 'sk-1234567890abdef',
            'engine': 'text-davinci-003',
            'max_tokens': 4000,
        } # openai
except Exception as e:
    logger.exception(e)
    sys.exit("RTFM")
