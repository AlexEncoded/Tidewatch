import ast
from pathlib import Path

from app.application.ports import DeviceHealthReader, MaintenanceReader
from app.application.sensor_health import SensorHealthCheckWriter
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
    assert "pydantic" not in modules


def test_application_does_not_depend_on_http_or_database_frameworks() -> None:
    modules = imported_modules(API_APP / "application")

    assert not any(module.startswith("app.models") for module in modules)
    assert "fastapi" not in modules
    assert "sqlalchemy" not in modules
    assert not any(module.endswith(".database") for module in modules)
    assert not any(module.endswith(".repository") for module in modules)


def test_repository_implements_the_maintenance_read_port() -> None:
    adapter = BuoyRepository.__new__(BuoyRepository)

    assert isinstance(adapter, MaintenanceReader)


def test_repository_implements_the_device_health_read_port() -> None:
    adapter = BuoyRepository.__new__(BuoyRepository)

    assert isinstance(adapter, DeviceHealthReader)


def test_repository_implements_the_sensor_health_writer_port() -> None:
    adapter = BuoyRepository.__new__(BuoyRepository)

    assert isinstance(adapter, SensorHealthCheckWriter)


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


def test_http_routers_do_not_construct_telemetry_response_models_for_writes() -> None:
    for source_file in (API_APP / "routers").glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        constructions = [
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id.endswith("Reading")
        ]
        assert not constructions, (
            f"{source_file.name} must map telemetry through application services; "
            f"found direct reading model construction: {constructions}"
        )


def test_repository_does_not_import_http_telemetry_reading_models() -> None:
    tree = ast.parse((API_APP / "repository.py").read_text(encoding="utf-8"))
    reading_models = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "models"
        for alias in node.names
        if alias.name.endswith("Reading")
    ]

    assert not reading_models


def test_quality_router_depends_on_application_port_not_repository_adapter() -> None:
    tree = ast.parse((API_APP / "routers" / "quality.py").read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "repository" not in imported_modules
    assert "application.ports" in imported_modules


def test_fleet_telemetry_router_depends_on_application_port_not_repository_adapter() -> None:
    tree = ast.parse((API_APP / "routers" / "telemetry.py").read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "repository" not in imported_modules
    assert "application.ports" in imported_modules


def test_movement_route_uses_injected_reader_and_not_repository_constructor() -> None:
    tree = ast.parse((API_APP / "routers" / "analytics.py").read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "buoy_movement_analysis"
    )
    calls = {
        node.func.id
        for node in ast.walk(route)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "BuoyRepository" not in calls
    assert "analyze_movement_for_buoy" in calls


def test_pressure_analysis_route_uses_injected_reader_not_repository_constructor() -> None:
    tree = ast.parse((API_APP / "routers" / "analytics.py").read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "pressure_analysis"
    )
    calls = {
        node.func.id
        for node in ast.walk(route)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "BuoyRepository" not in calls
    assert "analyze_pressure_for_buoy" in calls


def test_wave_analysis_route_uses_injected_reader_not_repository_constructor() -> None:
    tree = ast.parse((API_APP / "routers" / "analytics.py").read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "buoy_wave_analysis"
    )
    calls = {
        node.func.id
        for node in ast.walk(route)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "BuoyRepository" not in calls
    assert "analyze_wave_for_buoy" in calls


def test_temperature_analysis_route_uses_injected_reader_not_repository_constructor() -> None:
    tree = ast.parse((API_APP / "routers" / "analytics.py").read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "temperature_analysis"
    )
    calls = {
        node.func.id
        for node in ast.walk(route)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "BuoyRepository" not in calls
    assert "analyze_temperature_for_buoy" in calls


def test_temperature_alerts_route_delegates_to_application_service() -> None:
    tree = ast.parse((API_APP / "routers" / "analytics.py").read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "temperature_alerts"
    )
    calls = {
        node.func.id
        for node in ast.walk(route)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "BuoyRepository" not in calls
    assert "find_temperature_anomalies" in calls


def test_persisted_temperature_alert_routes_use_application_services() -> None:
    tree = ast.parse((API_APP / "routers" / "alerts.py").read_text(encoding="utf-8"))
    calls_by_route = {
        node.name: {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert "evaluate_and_store_temperature_alerts" in calls_by_route["evaluate_temperature_alerts"]
    assert "list_stored_temperature_alerts" in calls_by_route["stored_temperature_alerts"]
    assert "resolve_stored_temperature_alert" in calls_by_route["resolve_temperature_alert"]
    assert all("BuoyRepository" not in calls for calls in calls_by_route.values())


def test_analytics_router_has_no_database_or_repository_dependency() -> None:
    tree = ast.parse((API_APP / "routers" / "analytics.py").read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "repository" not in imported_modules
    assert "database" not in imported_modules
    assert "sqlalchemy.orm" not in imported_modules


def test_device_router_has_no_database_or_repository_dependency() -> None:
    tree = ast.parse((API_APP / "routers" / "devices.py").read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "repository" not in imported_modules
    assert "database" not in imported_modules
    assert "sqlalchemy.orm" not in imported_modules
    assert "entities" not in imported_modules


def test_buoy_location_routes_delegate_to_application_service():
    tree = ast.parse((API_APP / "routers" / "buoys.py").read_text(encoding="utf-8"))
    routes = {
        node.name: {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert "query_buoy_locations" in routes["list_buoy_locations"]
    assert "query_buoy_locations" in routes["export_buoy_locations"]
    assert all("BuoyRepository" not in routes[name] for name in (
        "list_buoy_locations",
        "export_buoy_locations",
    ))


def test_stale_buoy_route_delegates_to_application_service():
    tree = ast.parse((API_APP / "routers" / "buoys.py").read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "stale_buoys"
    )
    calls = {
        node.func.id
        for node in ast.walk(route)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "find_stale_buoys" in calls
    assert "BuoyRepository" not in calls


def test_buoy_status_route_delegates_to_application_service():
    tree = ast.parse((API_APP / "routers" / "buoys.py").read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "update_buoy_status"
    )
    calls = {
        node.func.id
        for node in ast.walk(route)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "change_buoy_status" in calls
    assert "BuoyRepository" not in calls


def test_buoy_location_update_route_delegates_to_application_service():
    tree = ast.parse((API_APP / "routers" / "buoys.py").read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "update_buoy_location"
    )
    calls = {
        node.func.id
        for node in ast.walk(route)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "record_buoy_location" in calls
    assert "BuoyRepository" not in calls


def test_buoy_creation_route_delegates_to_application_service():
    tree = ast.parse((API_APP / "routers" / "buoys.py").read_text(encoding="utf-8"))
    route = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "create_buoy"
    )
    calls = {
        node.func.id
        for node in ast.walk(route)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }

    assert "create_buoy_use_case" in calls
    assert "BuoyRepository" not in calls


def test_battery_routes_use_injected_telemetry_port():
    tree = ast.parse((API_APP / "routers" / "battery.py").read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    routes = {
        node.name: {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert "repository" not in imported_modules
    assert "database" not in imported_modules
    assert all("BuoyRepository" not in calls for calls in routes.values())
    assert all("ensure_buoy_exists" in routes[name] for name in (
        "record_battery",
        "latest_battery",
        "battery_history",
        "battery_analysis",
        "battery_health",
    ))


def test_temperature_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_temperature", "list_temperatures"):
        route = routes[name]
        calls = {
            child.func.id
            for child in ast.walk(route)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        gateway_parameter = next(
            argument for argument in route.args.args if argument.arg == "gateway"
        )
        assert "BuoyRepository" not in calls
        assert isinstance(gateway_parameter.annotation, ast.Name)
        assert gateway_parameter.annotation.id == "TemperatureTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_temperature_telemetry_gateway" in imported_dependencies


def test_pressure_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_pressure", "list_pressures"):
        route = routes[name]
        calls = {
            child.func.id
            for child in ast.walk(route)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        gateway_parameter = next(
            argument for argument in route.args.args if argument.arg == "gateway"
        )
        assert "BuoyRepository" not in calls
        assert isinstance(gateway_parameter.annotation, ast.Name)
        assert gateway_parameter.annotation.id == "PressureTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_pressure_telemetry_gateway" in imported_dependencies


def test_salinity_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_salinity", "list_salinity"):
        route = routes[name]
        calls = {
            child.func.id
            for child in ast.walk(route)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        gateway_parameter = next(
            argument for argument in route.args.args if argument.arg == "gateway"
        )
        assert "BuoyRepository" not in calls
        assert isinstance(gateway_parameter.annotation, ast.Name)
        assert gateway_parameter.annotation.id == "SalinityTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_salinity_telemetry_gateway" in imported_dependencies


def test_imu_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_imu", "list_imu"):
        route = routes[name]
        calls = {
            child.func.id
            for child in ast.walk(route)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        gateway_parameter = next(
            argument for argument in route.args.args if argument.arg == "gateway"
        )
        assert "BuoyRepository" not in calls
        assert isinstance(gateway_parameter.annotation, ast.Name)
        assert gateway_parameter.annotation.id == "ImuTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_imu_telemetry_gateway" in imported_dependencies


def test_ambient_light_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_ambient_light", "list_ambient_light"):
        route = routes[name]
        calls = {
            child.func.id
            for child in ast.walk(route)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        gateway_parameter = next(
            argument for argument in route.args.args if argument.arg == "gateway"
        )
        assert "BuoyRepository" not in calls
        assert isinstance(gateway_parameter.annotation, ast.Name)
        assert gateway_parameter.annotation.id == "AmbientLightTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_ambient_light_telemetry_gateway" in imported_dependencies


def test_wind_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_wind", "list_wind"):
        route = routes[name]
        calls = {
            child.func.id
            for child in ast.walk(route)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        gateway_parameter = next(
            argument for argument in route.args.args if argument.arg == "gateway"
        )
        assert "BuoyRepository" not in calls
        assert isinstance(gateway_parameter.annotation, ast.Name)
        assert gateway_parameter.annotation.id == "WindTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_wind_telemetry_gateway" in imported_dependencies


def test_marine_current_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_marine_current", "list_marine_current"):
        route = routes[name]
        calls = {
            child.func.id
            for child in ast.walk(route)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        gateway_parameter = next(
            argument for argument in route.args.args if argument.arg == "gateway"
        )
        assert "BuoyRepository" not in calls
        assert isinstance(gateway_parameter.annotation, ast.Name)
        assert gateway_parameter.annotation.id == "MarineCurrentTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_marine_current_telemetry_gateway" in imported_dependencies
