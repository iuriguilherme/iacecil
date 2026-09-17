"""`python -m iacecil <mode>` dispatch (R6).

Production is three supervised sibling processes now. Every other mode
must keep booting exactly what it booted before, so these tests pin the
whole dispatch table rather than only the branch that changed.
"""

import ast
import inspect

import pytest


def dispatch_source() -> str:
    import iacecil.__main__ as main_module

    return inspect.getsource(main_module)


def test_production_starts_the_supervisor():
    """R6: production no longer imports the fused runner."""
    source = dispatch_source()

    assert 'from .controllers._iacecil.supervisor import run_app' in source
    assert 'from .controllers._iacecil import production' not in source


@pytest.mark.parametrize('mode, expected', [
    ('connectors', 'connectors_runner'),
    ('connectors_v3', 'connectors_v3_runner'),
    ('fpersonas', 'fpersonas'),
    ('furhatgpt', 'furhatgpt'),
])
def test_other_modes_are_untouched(mode, expected):
    source = dispatch_source()

    assert f"'{mode}'" in source
    assert expected in source


def test_testing_mode_is_still_the_default():
    source = dispatch_source()

    assert 'No arguments provided, using testing mode' in source
    assert 'from .controllers._iacecil.testing import run_app' in source


def test_web_unit_runs_the_web_only_entry():
    """The supervisor's web child calls run_web, so importing the
    production module no longer starts a server as a side effect."""
    from iacecil.controllers._iacecil import supervisor

    source = inspect.getsource(supervisor.web_unit)
    assert 'run_web' in source


def test_production_module_starts_nothing_on_import():
    """It used to run uvicorn at import time, which made it impossible
    to import from a supervisor child without serving."""
    import iacecil.controllers._iacecil.production as production_module

    tree = ast.parse(inspect.getsource(production_module))
    top_level_calls = [node for node in tree.body
        if isinstance(node, (ast.Expr, ast.Try, ast.Assign))]

    assert top_level_calls == [] or all(
        isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
        for node in top_level_calls), "production module still runs on import"
    assert hasattr(production_module, 'run_web')


def test_run_web_reads_its_own_argv():
    """R5: config crosses the process boundary as argv, and the child
    loads instance/ itself."""
    from iacecil.controllers._iacecil.production import run_web

    source = inspect.getsource(run_web)
    assert 'argv = list(argv) or list(sys.argv)' in source
    assert 'instance._bots_{argv[2]}' in source
