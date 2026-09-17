"""The web app owns no connector lifecycle (R2, R12).

Killing the web process must leave every bot serving. That holds only
if the web process never started them, so these tests assert on what the
serving hooks do *not* do.
"""

import ast
import inspect

import pytest

from iacecil.views.quart_app import quart_startup
from iacecil.views.quart_app.identity import (
    bot_id_from_token,
    build_bot_identities,
    identity_from_config,
)


class FakeConfig:
    def __init__(self, token='123456:secret', info=None):
        self.telegram = {'token': token}
        self.info = info or {}


def executable_names(function) -> set:
    """Every name and attribute the function actually executes.

    Read from the AST rather than the text, so the comments explaining
    what was removed do not count as doing it.
    """
    tree = ast.parse(inspect.getsource(function))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


def executable_strings(function) -> set:
    tree = ast.parse(inspect.getsource(function))
    strings = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.add(node.value)
    ## Docstrings describe the change; they are not behavior
    return {s for s in strings if len(s) < 200}


def test_serving_hooks_start_no_connectors_and_no_scheduler():
    """The whole coupling lived in these two functions."""
    names = executable_names(quart_startup)

    for forbidden in ('ConnectorManager', 'run_all', 'add_handlers',
            'add_filters', 'add_jobs', 'start_polling', 'scheduler'):
        assert forbidden not in names, f"web app still does {forbidden}"


def test_web_app_module_does_not_import_aiogram():
    """R2: no aiogram runtime in the web process."""
    import iacecil.views.quart_app as quart_app_module

    tree = ast.parse(inspect.getsource(quart_app_module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split('.')[0])

    assert 'aiogram' not in imported


def test_liveness_ping_is_not_sent_by_the_web_unit():
    """R12: the #on/#off ping belongs to the connector unit, so it
    reports connector liveness rather than web liveness."""
    assert 'send_message' not in executable_names(quart_startup)
    assert not [text for text in executable_strings(quart_startup)
        if 'Mãe tá' in text]


def test_quart_startup_takes_identities_not_dispatchers():
    parameters = list(
        inspect.signature(quart_startup).parameters)

    assert parameters == ['config', 'bot_identities']


def test_bot_id_comes_from_the_token_without_the_secret():
    assert bot_id_from_token('123456:AAHsecret') == '123456'
    assert bot_id_from_token('') == ''
    assert bot_id_from_token(None) == ''


def test_identity_reads_configuration_not_a_live_bot():
    identity = identity_from_config('mybot', FakeConfig(
        info={'first_name': 'Cecil', 'username': 'iacecilbot'}))

    assert identity['id'] == '123456'
    assert identity['name'] == 'mybot'
    assert identity['first_name'] == 'Cecil'
    assert identity['username'] == 'iacecilbot'
    ## Live polling state is connector-process knowledge (slice 2)
    assert identity['status'] is None


def test_identity_falls_back_to_the_bot_name():
    identity = identity_from_config('mybot', FakeConfig())

    assert identity['first_name'] == 'mybot'
    assert identity['username'] == 'mybot'


def test_one_broken_config_does_not_blank_the_page():
    class Broken:
        @property
        def telegram(self):
            raise ValueError('malformed config')

    identities = build_bot_identities({
        'good': FakeConfig(), 'broken': Broken()})

    assert [identity['name'] for identity in identities] == ['good']


def test_identities_keep_configuration_order():
    identities = build_bot_identities({
        'first': FakeConfig('1:a'),
        'second': FakeConfig('2:b'),
    })

    assert [identity['id'] for identity in identities] == ['1', '2']


def test_no_configured_bots_is_not_an_error():
    assert build_bot_identities({}) == []
    assert build_bot_identities(None) == []
