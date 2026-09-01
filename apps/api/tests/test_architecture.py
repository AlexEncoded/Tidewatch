import ast
from pathlib import Path


API_APP = Path(__file__).parents[1] / "app"


def imported_modules(directory: Path) -> set[str]:
    modules = set()
    for source_file in directory.glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
    return modules


def test_domain_does_not_depend_on_api_or_persistence_frameworks() -> None:
    modules = imported_modules(API_APP / "domain")

    assert not any(module.startswith("app.models") for module in modules)
    assert "fastapi" not in modules
    assert "sqlalchemy" not in modules


def test_application_does_not_depend_on_http_or_database_frameworks() -> None:
    modules = imported_modules(API_APP / "application")

    assert "fastapi" not in modules
    assert "sqlalchemy" not in modules
    assert not any(module.endswith(".database") for module in modules)
