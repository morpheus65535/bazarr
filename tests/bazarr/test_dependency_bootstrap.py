import ast
from pathlib import Path


def test_bootstrap_checks_msgspec_before_skipping_dependency_install() -> None:
    source = Path(__file__).resolve().parents[2] / 'bazarr' / 'init.py'
    tree = ast.parse(source.read_text())
    bootstrap = next(node for node in tree.body if isinstance(node, ast.If)
                     and ast.unparse(node.test) == 'not args.no_update')
    check = next(node for node in bootstrap.body if isinstance(node, ast.Try))
    imports = {alias.name for statement in check.body for node in ast.walk(statement)
               if isinstance(node, ast.Import) for alias in node.names}

    assert 'msgspec' in imports
