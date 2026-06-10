"""
Default configuration for any bot
Copy this file to instance/bots/default.py
"""

from pydantic_settings import BaseSettings

class DefaultBotConfig(BaseSettings):
    """Default bot configuration"""
    ## All plugins: 'default', 'admin', 'archive', 'cryptoforex',
    ## 'donate', 'echo', 'feedback', 'garimpo', 'greatful',
    ## 'hashes', 'mate_matica', 'natural', 'portaria',
    ## 'qr', 'storify', 'totalvoice', 'tropixel', 'tts',
    ## 'welcome', 'ytdl'
    ## FIXME: Some plugins currently will not work if loaded after
    ## others, have to find out which is the correct order.
    ## This assumes the current behaviour of ordered python lists.
    plugins: dict = {
        'all': [
            "default",
            "admin",
            "archive",
            "cryptoforex",
            "donate",
            "echo",
            "feedback",
            "garimpo",
            "greatful",
            "hashes",
            "mate_matica",
            "natural",
            "portaria",
            "qr",
            "storify",
            "totalvoice",
            "tropixel",
            "tts",
            "welcome",
            "ytdl",
            "deepseek",
        ], # all
        'enable': [
            "default",
            "admin",
        ], # enable
        'disable': [
        ], # disable
        'alpha': [
            "admin",
        ], # alpha
        'beta': [
            "admin",
        ], # beta
        'gamma': [
            "donate",
        ], # gamma
        'delta': [
            "personalidades",
            "feedback",
            "welcome",
        ], # delta
        'epsilon': [
            "archive",
            "hashes",
            "mate_matica",
            "qr",
            "ytdl",
        ], # epsilon
        'omega': [
            "telegram",
        ], # omega
    } # plugins
    info: dict = {
        'website': "garbage",
        'repository': "garbage",
    } # info
    
    ## Plugin donate - doações
    donate: dict = {
        'btc': 'garbage',
        'crypto': {
            'BCH': 'garbage',
            'BTC': 'garbage',
            'DOGE': 'garbage',
            'ETH': 'garbage',
            'FLO': 'garbage',
            'LTC': 'garbage',
            'PIVX': 'garbage',
            'TRX': 'garbage',
        },
    } # donate
    
    ## Plugin Tropixel
    tropixel: dict = {
        'site': "garbage",
        'boteco': "garbage",
    }
    ## Plugin personalidade
    ## List of working personalidades: 'iacecil', 'cryptoforex',
    ## 'default', 'matebot', 'metarec', 'pave', 'pacume', 'pasoca'
    personalidade: str = 'default'
    
    ## Plugin cryptoforex
    coinmarketcap: dict = {
        'token': 'garbage',
    } # coinmarketcap
    
    ## Plugin TextoTecidoPalavra
    tecido: dict = {
        'host': '127.0.0.1',
        'port': 3000,
    } # tecido
    
    ## Plugin web3_wrapper
    web3: dict = {
        'binance': {
            'bsc_mainnet': "garbage",
            'bsc_testnet': "garbage",
        }, # binance
        'infura': {
            'eth_mainnet': """garbage""",
            'eth2_mainnet': """garbage""",
            'filecoin': """garbage""",
        }, # infura
    } # web3
    
    ## Plugin tc
    serpapi: dict = {
        'api_key': """garbage""",
    } # serpapi
    ## Plugin calendar
    jobs: list = []
    timezone: str = 'America/Sao_Paulo'
    
    quart: dict = {}
    telegram: dict = {
        'token': None,
        'info': {
            'group': "garbage",
            'channel': "garbage",
            'admin': "garbage",
            'dev': "garbage",
        },
        'webhook': {
            'host': "garbage",
            'path': "garbage",
            'webapp': "garbage",
            'port': 1,
        }, # webhook
        ## Plugin portaria
        'unwanted': [
            "garbage",
            "garbage",
        ], # unwanted
        'users': {
            'alpha': [
                1,
                -1,
            ],
            'beta': [
                1,
                -1,
            ],
            'gamma': [
                1,
                -1,
            ],
            'delta': [
                1,
                -1,
            ],
            'epsilon': [
                777000, # services
                1,
                -1,
            ], # epsilon
            'tropixel': [
                1,
                -1,
            ], # tropixel
            'pegadinha': [
                1,
                -1,
            ], # pegadinha
            'garimpo': [
                1,
                -1,
            ],
            'special': {
                'services': 777000,
                'desobedientecivil': 1,
                'debug': -1,
                'feedback': -1,
                'info': -1,
                'test': -1,
                'log_test': -1,
                'garimpo': -1,
                'groupanonymousbot': 1,
                'Channel_Bot': 1,
            }, # special
        }, # users
    } # telegram
    discord: dict = {
        'token': None,
    } # discord
    furhat: dict = {
        'bot': "garbage",
        'address': "127.0.0.1",
        'voice': "Camila",
        'mask': "adult",
        'character': "Titan",
        'language': "pt-BR",
        'led': {'green': 0, 'red': 150, 'blue': 30},
        'attend': {'x': 0, 'y': 0, 'z': 0},
        'voice_url': "garbage",
        'recognizer': {
            ## https://cloud.google.com/speech/docs/getting-started
            'google': {
                'type': "garbage",
                'project_id': "garbage",
                'private_key_id': "garbage",
                'private_key': """garbage""",
                'client_email': """garbage""",
                'client_id': "garbage",
                'auth_uri': "garbage",
                'token_uri': "garbage",
                'auth_provider_x509_cert_url': """garbage""",
                'client_x509_cert_url': """garbage""",
            }, # google
            ## https://azure.microsoft.com/en-us/services/cognitive-ser\
            ## vices/speech-to-text/
            'microsoft': {}, # microsoft
        }, # recognizer
        'synthesizer': {
            ## https://aws.amazon.com/pt/polly/
            'amazon': {
                'secret': "garbage",
                'key': "garbage",
                'engine': "garbage",
            }, # amazon
            ## https://www.acapela-group.com/solutions/acapela-cloud/
            'acapela': {}, # acapela
        }, # synthesizer
        'extension': "wav",
        'output_format': "pcm",
    } # furhat
    deepseek: dict = {
        'ollama': {
            'host': "http://127.0.0.1:11434",
            'model': "deepseek-r1:1.5b",
        }, # ollama
    } # deepseek
