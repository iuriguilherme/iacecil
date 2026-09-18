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


def imported_modules() -> set:
    """Modules the dispatch table actually imports, read from the AST.

    A substring check against the module text passes on a line that is
    present but unreachable; the parsed import statements do not.
    """
    import iacecil.__main__ as main_module

    tree = ast.parse(inspect.getsource(main_module))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                modules.add(f"{node.module}.{alias.name}")
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def dispatch_modes() -> set:
    """Every mode string the dispatch table compares against."""
    import iacecil.__main__ as main_module

    tree = ast.parse(inspect.getsource(main_module))
    modes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            modes.add(node.value)
    return modes


def test_production_starts_the_supervisor():
    """R6: production no longer imports the fused runner."""
    modules = imported_modules()

    assert 'controllers._iacecil.supervisor.run_app' in modules
    assert not [m for m in modules
        if m.endswith('_iacecil.production') or m.endswith('.production')]


@pytest.mark.parametrize('mode, expected_module', [
    ('connectors', 'controllers._iacecil.connectors_runner.run_app'),
    ('connectors_v3', 'controllers._iacecil.connectors_v3_runner.run_app'),
    ('fpersonas', 'controllers._iacecil.fpersonas'),
    ('furhatgpt', 'controllers._iacecil.furhatgpt'),
    ('zeo', 'controllers._iacecil.zeo_runner.run_zeo'),
])
def test_every_mode_dispatches_to_its_runner(mode, expected_module):
    assert mode in dispatch_modes()
    assert expected_module in imported_modules()


def test_testing_mode_is_still_the_default():
    assert 'controllers._iacecil.testing.run_app' in imported_modules()
    assert 'No arguments provided, using testing mode' in dispatch_modes()


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
