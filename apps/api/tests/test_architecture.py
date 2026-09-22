import ast
from pathlib import Path

from app.application.ports import MaintenanceReader
from app.repository import BuoyRepository


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
    assert not any(module.endswith(".repository") for module in modules)


def test_repository_implements_the_maintenance_read_port() -> None:
    adapter = BuoyRepository.__new__(BuoyRepository)

    assert isinstance(adapter, MaintenanceReader)


def test_main_only_assembles_the_api_and_does_not_define_routes() -> None:
    tree = ast.parse((API_APP / "main.py").read_text(encoding="utf-8"))
    route_decorators = {"get", "post", "put", "patch", "delete"}

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                assert not (
                    isinstance(decorator.func.value, ast.Name)
                    and decorator.func.value.id == "app"
                    and decorator.func.attr in route_decorators
                )


def test_http_routers_do_not_import_other_http_adapters() -> None:
    for source_file in (API_APP / "routers").glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        assert not any(
            isinstance(node, ast.ImportFrom) and node.level == 1
            for node in ast.walk(tree)
        ), f"{source_file.name} must depend on application ports, not sibling routers"
