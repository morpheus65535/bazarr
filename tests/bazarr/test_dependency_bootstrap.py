import ast
from pathlib import Path


def test_bootstrap_checks_pydantic_dependencies_before_skipping_install() -> None:
    source = Path(__file__).resolve().parents[2] / 'bazarr' / 'init.py'
    tree = ast.parse(source.read_text())
    bootstrap = next(node for node in tree.body if isinstance(node, ast.If)
                     and ast.unparse(node.test) == 'not args.no_update')
    check = next(node for node in bootstrap.body if isinstance(node, ast.Try))
    assert any(isinstance(node, ast.ImportFrom) and node.module == 'pydantic'
               and any(alias.name == 'TypeAdapter' for alias in node.names)
               for statement in check.body for node in ast.walk(statement))
    errors = check.handlers[0].type
    assert isinstance(errors, ast.Tuple)
    assert {node.id for node in errors.elts if isinstance(node, ast.Name)} == {'ImportError', 'SystemError'}
