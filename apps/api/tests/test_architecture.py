import ast
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_type_hints

from app.domain import telemetry as domain_telemetry
from app.domain.telemetry_types import ReadingQuality, SensorChannel
from app.schemas import telemetry as telemetry_schemas
from app.schemas.battery import BatteryReadingCreate

from app.application.ports import (
    DeviceHealthReader,
    DatabaseHealthReader,
    BuoySummaryReader,
    MaintenanceReader,
    TelemetryIngestionGateway,
)
from app.application.sensor_health import SensorHealthCheckWriter
from app.buoy_activity_repository import BuoyActivityRepository
from app.buoy_location_repository import BuoyLocationRepository
from app.buoy_registry_repository import BuoyRegistryRepository
from app.buoy_summary_repository import BuoySummaryRepository
from app.device_repository import DeviceRepository
from app.repository import BuoyRepository
from app.temperature_alert_repository import TemperatureAlertRepository
from app.temperature_repository import TemperatureRepository
from app.pressure_repository import PressureRepository
from app.salinity_repository import SalinityRepository
from app.imu_repository import ImuRepository
from app.ambient_light_repository import AmbientLightRepository
from app.wind_repository import WindRepository
from app.marine_current_repository import MarineCurrentRepository
from app.turbidity_repository import TurbidityRepository
from app.dissolved_oxygen_repository import DissolvedOxygenRepository
from app.ph_repository import PHRepository
from app.conductivity_repository import ConductivityRepository
from app.chlorophyll_a_repository import ChlorophyllARepository
from app.rainfall_repository import RainfallRepository
from app.humidity_repository import HumidityRepository


API_APP = Path(__file__).parents[1] / "app"


def test_buoy_registry_operations_use_the_fleet_adapter() -> None:
    from app.adapter_dependencies import (
        get_buoy_registrar,
        get_buoy_status_registry,
    )

    class EmptySession:
        def scalars(self, query):
            return self

        def all(self):
            return []

    session = EmptySession()
    assert not hasattr(BuoyRepository, "register_buoy")
    assert not hasattr(BuoyRepository, "update_buoy_status")
    assert not hasattr(BuoyRepository, "list_buoys")
    assert isinstance(get_buoy_registrar(session), BuoyRegistryRepository)
    assert isinstance(get_buoy_status_registry(session), BuoyRegistryRepository)
    assert get_buoy_registrar(session).list_buoy_snapshots() == []


def test_buoy_repository_delegates_identity_lookups_to_registry() -> None:
    class RegistryAdapter:
        def get_buoy(self, buoy_id):
            return ("buoy", buoy_id)

        def buoy_exists(self, buoy_id):
            return buoy_id == "known"

    repository = BuoyRepository.__new__(BuoyRepository)
    repository.registry = RegistryAdapter()

    assert repository.get_buoy("known") == ("buoy", "known")
    assert repository.buoy_exists("known")
    assert not repository.buoy_exists("unknown")


def test_stale_buoy_queries_use_the_fleet_activity_adapter() -> None:
    from app.adapter_dependencies import get_stale_buoy_reader

    assert not hasattr(BuoyRepository, "list_buoy_activity")
    assert isinstance(get_stale_buoy_reader(object()), BuoyActivityRepository)


def test_buoy_location_updates_use_the_location_adapter() -> None:
    from app.adapter_dependencies import (
        get_buoy_location_updater,
        get_buoy_location_history_reader,
        get_fleet_location_reader,
        get_movement_analysis_reader,
        get_wave_analysis_reader,
    )

    assert not hasattr(BuoyRepository, "update_buoy_location")
    session = object()
    assert isinstance(get_buoy_location_updater(session), BuoyLocationRepository)
    assert isinstance(get_buoy_location_history_reader(session), BuoyLocationRepository)
    assert isinstance(get_fleet_location_reader(session), BuoyLocationRepository)
    assert isinstance(get_movement_analysis_reader(session), BuoyLocationRepository)
    wave_reader = get_wave_analysis_reader(session)
    assert isinstance(wave_reader, BuoyRepository)
    assert wave_reader.locations.db is session


def test_temperature_alert_ports_use_the_composed_alert_adapter() -> None:
    from app.adapter_dependencies import (
        get_temperature_alert_store,
        get_temperature_alerts_reader,
    )

    session = object()
    assert not hasattr(BuoyRepository, "find_alert")
    assert not hasattr(BuoyRepository, "list_buoy_identities")
    assert isinstance(get_temperature_alerts_reader(session), TemperatureAlertRepository)
    assert isinstance(get_temperature_alert_store(session), TemperatureAlertRepository)


def test_temperature_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import (
        get_temperature_analysis_reader,
        get_temperature_telemetry_gateway,
    )

    session = object()
    assert isinstance(get_temperature_telemetry_gateway(session), TemperatureRepository)
    assert isinstance(get_temperature_analysis_reader(session), TemperatureRepository)
    assert isinstance(BuoyRepository(session).temperature, TemperatureRepository)


def test_pressure_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import (
        get_pressure_analysis_reader,
        get_pressure_telemetry_gateway,
    )

    session = object()
    assert isinstance(get_pressure_telemetry_gateway(session), PressureRepository)
    assert isinstance(get_pressure_analysis_reader(session), PressureRepository)
    assert isinstance(BuoyRepository(session).pressure, PressureRepository)


def test_salinity_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_salinity_telemetry_gateway

    session = object()
    assert isinstance(get_salinity_telemetry_gateway(session), SalinityRepository)
    assert isinstance(BuoyRepository(session).salinity, SalinityRepository)


def test_imu_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_imu_telemetry_gateway

    session = object()
    assert isinstance(get_imu_telemetry_gateway(session), ImuRepository)
    assert isinstance(BuoyRepository(session).imu, ImuRepository)


def test_ambient_light_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_ambient_light_telemetry_gateway

    session = object()
    assert isinstance(
        get_ambient_light_telemetry_gateway(session), AmbientLightRepository
    )
    assert isinstance(BuoyRepository(session).ambient_light, AmbientLightRepository)


def test_wind_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_wind_telemetry_gateway

    session = object()
    assert isinstance(get_wind_telemetry_gateway(session), WindRepository)
    assert isinstance(BuoyRepository(session).wind, WindRepository)


def test_marine_current_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_marine_current_telemetry_gateway

    session = object()
    assert isinstance(
        get_marine_current_telemetry_gateway(session), MarineCurrentRepository
    )
    assert isinstance(BuoyRepository(session).marine_current, MarineCurrentRepository)


def test_turbidity_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_turbidity_telemetry_gateway

    session = object()
    assert isinstance(get_turbidity_telemetry_gateway(session), TurbidityRepository)
    assert isinstance(BuoyRepository(session).turbidity, TurbidityRepository)


def test_dissolved_oxygen_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_dissolved_oxygen_telemetry_gateway

    session = object()
    assert isinstance(
        get_dissolved_oxygen_telemetry_gateway(session), DissolvedOxygenRepository
    )
    assert isinstance(
        BuoyRepository(session).dissolved_oxygen, DissolvedOxygenRepository
    )


def test_ph_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_ph_telemetry_gateway

    session = object()
    assert isinstance(get_ph_telemetry_gateway(session), PHRepository)
    assert isinstance(BuoyRepository(session).ph, PHRepository)


def test_conductivity_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_conductivity_telemetry_gateway

    session = object()
    assert isinstance(
        get_conductivity_telemetry_gateway(session), ConductivityRepository
    )
    assert isinstance(BuoyRepository(session).conductivity, ConductivityRepository)


def test_chlorophyll_a_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_chlorophyll_a_telemetry_gateway

    session = object()
    assert isinstance(
        get_chlorophyll_a_telemetry_gateway(session), ChlorophyllARepository
    )
    assert isinstance(BuoyRepository(session).chlorophyll_a, ChlorophyllARepository)


def test_rainfall_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_rainfall_telemetry_gateway

    session = object()
    assert isinstance(get_rainfall_telemetry_gateway(session), RainfallRepository)
    assert isinstance(BuoyRepository(session).rainfall, RainfallRepository)


def test_humidity_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_humidity_telemetry_gateway

    session = object()
    assert isinstance(get_humidity_telemetry_gateway(session), HumidityRepository)
    assert isinstance(BuoyRepository(session).humidity, HumidityRepository)


def test_buoy_repository_composes_device_repository_for_compatibility() -> None:
    class DeviceAdapter:
        def get_device(self, device_id):
            return ("device", device_id)

        def get_device_snapshot(self, device_id):
            return ("snapshot", device_id)

        def list_device_snapshots(self, buoy_id):
            return [("snapshots", buoy_id)]

        def mark_device_seen_by_id(self, device_id, seen_at):
            return ("seen", device_id, seen_at)

    repository = BuoyRepository.__new__(BuoyRepository)
    repository.devices = DeviceAdapter()

    assert not issubclass(BuoyRepository, DeviceRepository)
    assert repository.get_device("unit-a") == ("device", "unit-a")
    assert repository.get_device_snapshot("unit-a") == ("snapshot", "unit-a")
    assert repository.list_device_snapshots("buoy-a") == [("snapshots", "buoy-a")]
    assert repository.mark_device_seen_by_id("unit-a", "now") == (
        "seen",
        "unit-a",
        "now",
    )


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


def imports_package(modules: set[str], package: str) -> bool:
    return any(module == package or module.startswith(f"{package}.") for module in modules)


def test_domain_does_not_depend_on_api_or_persistence_frameworks() -> None:
    modules = imported_modules(API_APP / "domain")

    assert not imports_package(modules, "app.models")
    assert not imports_package(modules, "app.entities")
    assert not imports_package(modules, "app.schemas")
    assert not imports_package(modules, "fastapi")
    assert not imports_package(modules, "sqlalchemy")
    assert not imports_package(modules, "pydantic")


def test_application_does_not_depend_on_http_or_database_frameworks() -> None:
    modules = imported_modules(API_APP / "application")

    assert not imports_package(modules, "app.models")
    assert not imports_package(modules, "app.entities")
    assert not imports_package(modules, "app.schemas")
    assert not imports_package(modules, "fastapi")
    assert not imports_package(modules, "sqlalchemy")
    assert not imports_package(modules, "pydantic")
    assert "os" not in modules
    assert not any(module.endswith(".database") for module in modules)
    assert not any(module.endswith(".repository") for module in modules)
    forbidden_adapters = {
        "adapter_dependencies",
        "entities",
        "main",
        "metrics",
        "routers",
    }
    assert not any(
        module.rsplit(".", 1)[-1] in forbidden_adapters for module in modules
    )


def test_analytics_adapter_does_not_use_the_legacy_models_facade() -> None:
    analytics_module = ast.parse((API_APP / "analytics.py").read_text(encoding="utf-8"))
    imported = {
        node.module
        for node in ast.walk(analytics_module)
        if isinstance(node, ast.ImportFrom)
    }
    assert "models" not in imported


def test_telemetry_schemas_and_domain_snapshots_share_channel_and_quality_types() -> None:
    reading_schemas = [
        model
        for model in vars(telemetry_schemas).values()
        if isinstance(model, type)
        and model.__module__ == telemetry_schemas.__name__
        and model.__name__.endswith("ReadingCreate")
        and "sensor_channel" in model.model_fields
    ]
    assert reading_schemas
    for model in reading_schemas:
        assert model.model_fields["sensor_channel"].annotation is SensorChannel
        assert model.model_fields["quality"].annotation is ReadingQuality

    assert BatteryReadingCreate.model_fields["device_id"].annotation is SensorChannel

    domain_snapshots = [
        model
        for model in vars(domain_telemetry).values()
        if isinstance(model, type)
        and is_dataclass(model)
        and model.__module__ == domain_telemetry.__name__
        and model.__name__.endswith("TelemetrySnapshot")
    ]
    for model in domain_snapshots:
        annotations = get_type_hints(model)
        if "sensor_channel" in annotations:
            assert annotations["sensor_channel"] is SensorChannel
            assert annotations["quality"] is ReadingQuality


def test_imports_package_recognizes_nested_framework_modules() -> None:
    assert imports_package({"sqlalchemy.orm", "typing"}, "sqlalchemy")
    assert not imports_package({"sqlalchemy.orm", "typing"}, "fastapi")


def test_device_http_contracts_are_outside_the_general_models_module() -> None:
    device_router = ast.parse(
        (API_APP / "routers" / "devices.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module for node in ast.walk(device_router) if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.devices" in imported_modules
    assert "models" not in imported_modules

    model_tree = ast.parse((API_APP / "models.py").read_text(encoding="utf-8"))
    model_names = {
        node.name for node in model_tree.body if isinstance(node, ast.ClassDef)
    }
    assert not model_names.intersection(
        {"DeviceCreate", "DeviceStatusUpdate", "Device", "DeviceHealth"}
    )


def test_fleet_http_contracts_are_outside_the_general_models_module() -> None:
    buoy_router = ast.parse(
        (API_APP / "routers" / "buoys.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module for node in ast.walk(buoy_router) if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.fleet" in imported_modules

    model_tree = ast.parse((API_APP / "models.py").read_text(encoding="utf-8"))
    model_names = {
        node.name for node in model_tree.body if isinstance(node, ast.ClassDef)
    }
    assert not model_names.intersection(
        {
            "BuoyCreate",
            "BuoyStatusUpdate",
            "BuoyLocationUpdate",
            "BuoyLocationReadingCreate",
            "BuoyLocationReading",
            "Buoy",
            "BuoyHealth",
        }
    )


def test_quality_http_contract_is_outside_the_general_models_module() -> None:
    quality_router = ast.parse(
        (API_APP / "routers" / "quality.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(quality_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.quality" in imported_modules

    model_tree = ast.parse((API_APP / "models.py").read_text(encoding="utf-8"))
    model_names = {
        node.name for node in model_tree.body if isinstance(node, ast.ClassDef)
    }
    assert "QualitySummary" not in model_names


def test_battery_http_contracts_are_outside_the_general_models_module() -> None:
    battery_router = ast.parse(
        (API_APP / "routers" / "battery.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(battery_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.battery" in imported_modules

    model_tree = ast.parse((API_APP / "models.py").read_text(encoding="utf-8"))
    model_names = {
        node.name for node in model_tree.body if isinstance(node, ast.ClassDef)
    }
    assert not model_names.intersection(
        {
            "BatteryReadingCreate",
            "BatteryReading",
            "BatteryHealth",
            "BatteryAnalysis",
        }
    )


def test_analytics_http_contracts_are_outside_the_general_models_module() -> None:
    analytics_router = ast.parse(
        (API_APP / "routers" / "analytics.py").read_text(encoding="utf-8")
    )
    alert_router = ast.parse(
        (API_APP / "routers" / "alerts.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for tree in (analytics_router, alert_router)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.analytics" in imported_modules

    model_tree = ast.parse((API_APP / "models.py").read_text(encoding="utf-8"))
    model_names = {
        node.name for node in model_tree.body if isinstance(node, ast.ClassDef)
    }
    assert not model_names.intersection(
        {
            "PressureAnalysis",
            "WaveAnalysis",
            "MovementAnalysis",
            "TemperatureAnalysis",
            "TemperatureAlert",
            "StoredTemperatureAlert",
        }
    )


def test_sensor_health_http_contracts_are_outside_the_general_models_module() -> None:
    sensor_router = ast.parse(
        (API_APP / "routers" / "sensors.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(sensor_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.sensors" in imported_modules

    model_tree = ast.parse((API_APP / "models.py").read_text(encoding="utf-8"))
    model_names = {
        node.name for node in model_tree.body if isinstance(node, ast.ClassDef)
    }
    assert not model_names.intersection({"SensorHealth", "SensorHealthCheck"})


def test_maintenance_http_contracts_are_outside_the_general_models_module() -> None:
    maintenance_router = ast.parse(
        (API_APP / "routers" / "maintenance.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(maintenance_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.maintenance" in imported_modules

    model_tree = ast.parse((API_APP / "models.py").read_text(encoding="utf-8"))
    model_names = {
        node.name for node in model_tree.body if isinstance(node, ast.ClassDef)
    }
    assert not model_names.intersection(
        {"MaintenanceIssue", "MaintenanceNotificationResult"}
    )


def test_telemetry_response_contract_is_outside_the_general_models_module() -> None:
    ingestion_router = ast.parse(
        (API_APP / "routers" / "ingestion.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(ingestion_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.telemetry" in imported_modules

    model_tree = ast.parse((API_APP / "models.py").read_text(encoding="utf-8"))
    model_names = {
        node.name for node in model_tree.body if isinstance(node, ast.ClassDef)
    }
    assert "TelemetryIngestResponse" not in model_names


def test_core_sensor_http_contracts_are_outside_the_general_models_module() -> None:
    sensor_router = ast.parse(
        (API_APP / "routers" / "sensors.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(sensor_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.telemetry" in imported_modules

    ingestion_router = ast.parse(
        (API_APP / "routers" / "ingestion.py").read_text(encoding="utf-8")
    )
    ingestion_imports = {
        node.module
        for node in ast.walk(ingestion_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.ingestion" in ingestion_imports

    fleet_router = ast.parse((API_APP / "routers" / "buoys.py").read_text(encoding="utf-8"))
    fleet_imports = {
        node.module
        for node in ast.walk(fleet_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.fleet_summary" in fleet_imports

    model_tree = ast.parse((API_APP / "models.py").read_text(encoding="utf-8"))
    model_names = {
        node.name for node in model_tree.body if isinstance(node, ast.ClassDef)
    }
    assert not model_names.intersection(
        {
            "TemperatureReadingCreate",
            "TemperatureReading",
            "PressureReadingCreate",
            "PressureReading",
            "SalinityReadingCreate",
            "SalinityReading",
            "ImuReadingCreate",
            "ImuReading",
            "AmbientLightReadingCreate",
            "AmbientLightReading",
            "WindReadingCreate",
            "WindReading",
            "MarineCurrentReadingCreate",
            "MarineCurrentReading",
            "TurbidityReadingCreate",
            "TurbidityReading",
            "DissolvedOxygenReadingCreate",
            "DissolvedOxygenReading",
            "PHReadingCreate",
            "PHReading",
            "ConductivityReadingCreate",
            "ConductivityReading",
            "ChlorophyllAReadingCreate",
            "ChlorophyllAReading",
            "RainfallReadingCreate",
            "RainfallReading",
            "HumidityReadingCreate",
            "HumidityReading",
            "AirTemperatureReadingCreate",
            "AirTemperatureReading",
            "AtmosphericPressureReadingCreate",
            "AtmosphericPressureReading",
            "AcousticAltimeterReadingCreate",
            "AcousticAltimeterReading",
            "UnderwaterAcousticReadingCreate",
            "UnderwaterAcousticReading",
            "TelemetryBatchCreate",
            "BuoySummary",
        }
    )


def test_repository_implements_the_maintenance_read_port() -> None:
    adapter = BuoyRepository.__new__(BuoyRepository)

    assert isinstance(adapter, MaintenanceReader)


def test_repository_implements_the_device_health_read_port() -> None:
    adapter = BuoyRepository.__new__(BuoyRepository)

    assert isinstance(adapter, DeviceHealthReader)


def test_repository_implements_the_sensor_health_writer_port() -> None:
    adapter = BuoyRepository.__new__(BuoyRepository)

    assert isinstance(adapter, SensorHealthCheckWriter)


def test_repository_implements_the_batch_ingestion_gateway() -> None:
    adapter = BuoyRepository.__new__(BuoyRepository)

    assert isinstance(adapter, TelemetryIngestionGateway)


def test_batch_ingestion_route_uses_injected_gateway() -> None:
    tree = ast.parse((API_APP / "routers" / "ingestion.py").read_text(encoding="utf-8"))
    route = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "ingest_telemetry"
    )
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
    assert gateway_parameter.annotation.id == "TelemetryIngestionGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_telemetry_ingestion_gateway" in imported_dependencies


def test_database_health_route_uses_injected_reader() -> None:
    tree = ast.parse((API_APP / "routers" / "system.py").read_text(encoding="utf-8"))
    route = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "health"
    )
    calls = {
        child.func.id
        for child in ast.walk(route)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    reader_parameter = next(
        argument for argument in route.args.args if argument.arg == "reader"
    )
    assert "text" not in calls
    assert isinstance(reader_parameter.annotation, ast.Name)
    assert reader_parameter.annotation.id == "DatabaseHealthReader"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_database_health_reader" in imported_dependencies


def test_buoy_summary_port_uses_composed_fleet_adapter() -> None:
    from app.adapter_dependencies import get_buoy_summary_reader

    adapter = get_buoy_summary_reader(object())

    assert not hasattr(BuoyRepository, "list_buoy_summaries")
    assert isinstance(adapter, BuoySummaryRepository)
    assert isinstance(adapter, BuoySummaryReader)


def test_buoy_summary_route_uses_injected_reader() -> None:
    tree = ast.parse((API_APP / "routers" / "buoys.py").read_text(encoding="utf-8"))
    route = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "list_buoys"
    )
    calls = {
        child.func.id
        for child in ast.walk(route)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    reader_parameter = next(
        argument for argument in route.args.args if argument.arg == "reader"
    )
    assert "BuoyRepository" not in calls
    assert isinstance(reader_parameter.annotation, ast.Name)
    assert reader_parameter.annotation.id == "BuoySummaryReader"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_buoy_summary_reader" in imported_dependencies


def test_maintenance_routes_use_injected_reader() -> None:
    tree = ast.parse((API_APP / "routers" / "maintenance.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    for name in ("maintenance_issues", "notify_maintenance"):
        route = routes[name]
        calls = {
            child.func.id
            for child in ast.walk(route)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }
        reader_parameter = next(
            argument for argument in route.args.args if argument.arg == "reader"
        )
        assert "BuoyRepository" not in calls
        assert "maintenance_issues" not in calls
        assert isinstance(reader_parameter.annotation, ast.Name)
        assert reader_parameter.annotation.id == "MaintenanceReader"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_maintenance_reader" in imported_dependencies


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


def test_http_routers_do_not_import_persistence_adapters() -> None:
    for source_file in (API_APP / "routers").glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert "sqlalchemy.orm" not in modules
        assert "database" not in modules
        assert "repository" not in modules


def test_repository_does_not_import_http_telemetry_reading_models() -> None:
    tree = ast.parse((API_APP / "repository.py").read_text(encoding="utf-8"))
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    reading_models = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "models"
        for alias in node.names
        if alias.name.endswith("Reading")
    ]

    assert not reading_models
    assert not imports_package(imported, "schemas")
    assert not imports_package(imported, "fastapi")
    assert not imports_package(imported, "pydantic")


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


def test_turbidity_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_turbidity", "list_turbidity"):
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
        assert gateway_parameter.annotation.id == "TurbidityTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_turbidity_telemetry_gateway" in imported_dependencies


def test_dissolved_oxygen_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_dissolved_oxygen", "list_dissolved_oxygen"):
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
        assert gateway_parameter.annotation.id == "DissolvedOxygenTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_dissolved_oxygen_telemetry_gateway" in imported_dependencies


def test_ph_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_ph", "list_ph"):
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
        assert gateway_parameter.annotation.id == "PHTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_ph_telemetry_gateway" in imported_dependencies


def test_conductivity_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_conductivity", "list_conductivity"):
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
        assert gateway_parameter.annotation.id == "ConductivityTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_conductivity_telemetry_gateway" in imported_dependencies


def test_chlorophyll_a_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_chlorophyll_a", "list_chlorophyll_a"):
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
        assert gateway_parameter.annotation.id == "ChlorophyllATelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_chlorophyll_a_telemetry_gateway" in imported_dependencies


def test_rainfall_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_rainfall", "list_rainfall"):
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
        assert gateway_parameter.annotation.id == "RainfallTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_rainfall_telemetry_gateway" in imported_dependencies


def test_humidity_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_humidity", "list_humidity"):
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
        assert gateway_parameter.annotation.id == "HumidityTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_humidity_telemetry_gateway" in imported_dependencies


def test_air_temperature_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_air_temperature", "list_air_temperature"):
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
        assert gateway_parameter.annotation.id == "AirTemperatureTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_air_temperature_telemetry_gateway" in imported_dependencies


def test_atmospheric_pressure_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_atmospheric_pressure", "list_atmospheric_pressure"):
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
        assert gateway_parameter.annotation.id == "AtmosphericPressureTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_atmospheric_pressure_telemetry_gateway" in imported_dependencies


def test_acoustic_altimeter_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_acoustic_altimeter", "list_acoustic_altimeter"):
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
        assert gateway_parameter.annotation.id == "AcousticAltimeterTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_acoustic_altimeter_telemetry_gateway" in imported_dependencies


def test_underwater_acoustic_routes_use_injected_telemetry_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    routes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    for name in ("record_underwater_acoustic", "list_underwater_acoustic"):
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
        assert gateway_parameter.annotation.id == "UnderwaterAcousticTelemetryGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_underwater_acoustic_telemetry_gateway" in imported_dependencies


def test_sensor_health_route_uses_injected_reader():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    route = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "sensor_health"
    )
    calls = {
        child.func.id
        for child in ast.walk(route)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    reader_parameter = next(
        argument for argument in route.args.args if argument.arg == "reader"
    )
    assert "BuoyRepository" not in calls
    assert isinstance(reader_parameter.annotation, ast.Name)
    assert reader_parameter.annotation.id == "SensorHealthReader"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_sensor_health_reader" in imported_dependencies


def test_sensor_health_history_route_uses_injected_reader():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    route = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "sensor_health_history"
    )
    calls = {
        child.func.id
        for child in ast.walk(route)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    reader_parameter = next(
        argument for argument in route.args.args if argument.arg == "reader"
    )
    assert "BuoyRepository" not in calls
    assert isinstance(reader_parameter.annotation, ast.Name)
    assert reader_parameter.annotation.id == "SensorHealthReader"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_sensor_health_reader" in imported_dependencies


def test_sensor_health_check_route_uses_injected_gateway():
    tree = ast.parse((API_APP / "routers" / "sensors.py").read_text(encoding="utf-8"))
    route = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "record_sensor_health_check"
    )
    calls = {
        child.func.id
        for child in ast.walk(route)
        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
    }
    gateway_parameter = next(
        argument for argument in route.args.args if argument.arg == "gateway"
    )
    assert "BuoyRepository" not in calls
    assert "sensor_health" not in calls
    assert isinstance(gateway_parameter.annotation, ast.Name)
    assert gateway_parameter.annotation.id == "SensorHealthCheckGateway"

    imported_dependencies = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == "adapter_dependencies"
        for alias in node.names
    }
    assert "get_sensor_health_check_gateway" in imported_dependencies
