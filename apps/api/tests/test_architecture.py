import ast
from dataclasses import is_dataclass
from pathlib import Path
from typing import get_type_hints

from app.domain import telemetry as domain_telemetry
from app.domain.telemetry_types import ReadingQuality, SensorChannel
from app.schemas import telemetry as telemetry_schemas
from app.schemas.battery import BatteryReadingCreate

from app.application.fleet_ports import BuoySummaryReader
from app.application.maintenance_ports import MaintenanceReader
from app.application.system_ports import DatabaseHealthReader
from app.application.telemetry_ports import (
    TelemetryIngestionGateway,
    TelemetryIngestionJobStore,
)
from app.buoy_activity_repository import BuoyActivityRepository
from app.buoy_location_repository import BuoyLocationRepository
from app.buoy_registry_repository import BuoyRegistryRepository
from app.buoy_summary_repository import BuoySummaryRepository
from app.device_repository import DeviceRepository
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
from app.air_temperature_repository import AirTemperatureRepository
from app.atmospheric_pressure_repository import AtmosphericPressureRepository
from app.acoustic_altimeter_repository import AcousticAltimeterRepository
from app.underwater_acoustic_repository import UnderwaterAcousticRepository
from app.battery_repository import BatteryRepository
from app.sensor_health_repository import SensorHealthRepository
from app.quality_summary_repository import QualitySummaryRepository
from app.telemetry_ingestion_repository import TelemetryIngestionRepository
from app.maintenance_repository import MaintenanceRepository
from app.wave_analysis_repository import WaveAnalysisRepository


API_APP = Path(__file__).parents[1] / "app"


def test_legacy_analytics_adapter_module_is_removed() -> None:
    assert not (API_APP / "analytics.py").exists()


def test_legacy_models_facade_module_is_removed() -> None:
    assert not (API_APP / "models.py").exists()


def test_fleet_persistence_entities_are_grouped_by_context() -> None:
    from app.fleet_entities import BuoyEntity
    from app.fleet_entities import (
        BatteryReadingEntity,
        BuoyEntity,
        BuoyLocationReadingEntity,
        DeviceEntity,
    )

    assert BuoyEntity.__module__ == "app.fleet_entities"
    assert DeviceEntity.__module__ == "app.fleet_entities"
    assert BuoyLocationReadingEntity.__module__ == "app.fleet_entities"
    assert BatteryReadingEntity.__module__ == "app.fleet_entities"
    assert set(BuoyEntity.__mapper__.relationships.keys()) == {
        "battery_readings",
        "devices",
        "location_readings",
    }


def test_sensor_orm_mappings_keep_foreign_keys_without_fleet_relationships() -> None:
    from app import sensor_entities

    sensor_mappings = [
        mapping
        for mapping in vars(sensor_entities).values()
        if getattr(mapping, "__module__", None) == sensor_entities.__name__
        and hasattr(mapping, "__table__")
    ]

    assert sensor_mappings
    for mapping in sensor_mappings:
        assert not mapping.__mapper__.relationships
        assert mapping.__table__.c.buoy_id.foreign_keys
        assert {
            foreign_key.target_fullname
            for foreign_key in mapping.__table__.c.buoy_id.foreign_keys
        } == {"buoys.id"}


def test_buoy_summary_adapter_consumes_domain_snapshots_not_orm_entities() -> None:
    source = (API_APP / "buoy_summary_repository.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "buoy_snapshot" not in imported_names
    assert "list_buoy_snapshots" in called_attributes


def test_buoy_registry_keeps_orm_entity_queries_private() -> None:
    source = (API_APP / "buoy_registry_repository.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    registry_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "BuoyRegistryRepository"
    )
    method_names = {
        node.name for node in registry_class.body if isinstance(node, ast.FunctionDef)
    }

    assert "get_buoy" not in method_names
    assert "list_buoys" not in method_names
    assert "_get_buoy_entity" in method_names
    assert "_list_buoy_entities" in method_names
    assert "list_buoy_snapshots" in method_names


def test_device_repository_keeps_orm_entity_queries_private() -> None:
    source = (API_APP / "device_repository.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    repository_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "DeviceRepository"
    )
    method_names = {
        node.name
        for node in repository_class.body
        if isinstance(node, ast.FunctionDef)
    }

    assert {"create_device", "list_devices", "get_device", "mark_device_seen"}.isdisjoint(
        method_names
    )
    assert "get_device_snapshot" in method_names
    assert "list_device_snapshots" in method_names
    assert "create_device_snapshot" in method_names


def test_public_repository_contracts_do_not_expose_orm_entities() -> None:
    for path in API_APP.glob("*_repository.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for repository in (
            node for node in tree.body if isinstance(node, ast.ClassDef)
        ):
            for method in (
                node
                for node in repository.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not node.name.startswith("_")
            ):
                annotations = [method.returns]
                arguments = [
                    argument.annotation
                    for argument in (
                        *method.args.posonlyargs,
                        *method.args.args,
                        *method.args.kwonlyargs,
                    )
                ]
                if method.args.vararg is not None:
                    arguments.append(method.args.vararg.annotation)
                if method.args.kwarg is not None:
                    arguments.append(method.args.kwarg.annotation)
                annotations.extend(arguments)
                exposed_entities = {
                    name.id
                    for annotation in annotations
                    if annotation is not None
                    for name in ast.walk(annotation)
                    if isinstance(name, ast.Name) and name.id.endswith("Entity")
                }
                assert not exposed_entities, (
                    f"{path.name}.{repository.name}.{method.name} exposes "
                    f"ORM entities: {sorted(exposed_entities)}"
                )


def test_location_ingestion_gateway_returns_domain_snapshot_not_orm_entity() -> None:
    source = (API_APP / "telemetry_ingestion_repository.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    add_location = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "add_location"
    )

    assert "BuoyLocationReadingEntity" not in imported_names
    assert isinstance(add_location.returns, ast.Name)
    assert add_location.returns.id == "LocationTelemetrySnapshot"


def test_domain_and_application_layers_avoid_framework_and_persistence_imports() -> None:
    for layer in ("domain", "application"):
        for path in (API_APP / layer).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported_modules = {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            imported_modules.update(
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            )
            imported_roots = {
                alias.name.split(".", maxsplit=1)[0]
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }

            assert not imported_roots.intersection({"sqlalchemy", "fastapi"}), path
            assert not any(
                module.split(".")[-1].endswith("entities")
                or module.split(".")[-1] == "schemas"
                or module in {"fastapi", "sqlalchemy"}
                or module.split(".")[-1].endswith("_repository")
                for module in imported_modules
            ), path


def test_http_routers_do_not_import_orm_entities_or_sqlalchemy() -> None:
    for path in (API_APP / "routers").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        imported_roots = {
            alias.name.split(".", maxsplit=1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }

        assert "sqlalchemy" not in imported_roots, path
        assert not any(
            module.split(".")[-1].endswith("entities")
            or module.split(".")[-1] == "sqlalchemy"
            for module in imported_modules
        ), path


def test_sensor_adapters_delegate_buoy_heartbeat_to_fleet_repository() -> None:
    for module_name in (
        "temperature_repository.py",
        "pressure_repository.py",
        "salinity_repository.py",
        "dissolved_oxygen_repository.py",
        "conductivity_repository.py",
        "ph_repository.py",
        "chlorophyll_a_repository.py",
        "turbidity_repository.py",
        "rainfall_repository.py",
        "humidity_repository.py",
        "air_temperature_repository.py",
        "atmospheric_pressure_repository.py",
        "imu_repository.py",
        "ambient_light_repository.py",
        "wind_repository.py",
        "marine_current_repository.py",
        "acoustic_altimeter_repository.py",
        "underwater_acoustic_repository.py",
        "battery_repository.py",
    ):
        tree = ast.parse((API_APP / module_name).read_text(encoding="utf-8"))
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert "get_buoy" not in called_attributes
        assert "mark_buoy_seen_by_id" in called_attributes


def test_alert_and_ingestion_job_entities_are_grouped_by_context() -> None:
    from app.alert_entities import TemperatureAlertEntity
    from app.telemetry_entities import TelemetryIngestionJobEntity

    assert TemperatureAlertEntity.__module__ == "app.alert_entities"
    assert TelemetryIngestionJobEntity.__module__ == "app.telemetry_entities"


def test_telemetry_ports_are_grouped_by_context() -> None:
    from app.application.telemetry_ports import (
        TelemetryBatchUnitOfWork,
        TelemetryIngestionJobStore,
        TelemetryMetrics,
        TelemetryQueueMetricsReader,
        TelemetryIngestionGateway,
    )

    assert TelemetryBatchUnitOfWork.__module__ == "app.application.telemetry_ports"
    assert TelemetryIngestionJobStore.__module__ == "app.application.telemetry_ports"
    assert TelemetryMetrics.__module__ == "app.application.telemetry_ports"
    assert TelemetryQueueMetricsReader.__module__ == "app.application.telemetry_ports"
    assert TelemetryIngestionGateway.__module__ == "app.application.telemetry_ports"


def test_fleet_ports_are_grouped_by_context() -> None:
    from app.application.fleet_ports import (
        BuoyLocationHistoryReader,
        BuoyLocationUpdater,
        BuoyRegistrar,
        BuoyStatusRegistry,
        BuoySummaryReader,
        FleetLocationReader,
        LocationTelemetryReader,
        MovementAnalysisReader,
        StaleBuoyReader,
    )

    for port in (
        BuoyLocationHistoryReader,
        BuoyLocationUpdater,
        BuoyRegistrar,
        BuoyStatusRegistry,
        BuoySummaryReader,
        FleetLocationReader,
        LocationTelemetryReader,
        MovementAnalysisReader,
        StaleBuoyReader,
    ):
        assert port.__module__ == "app.application.fleet_ports"


def test_analysis_ports_are_grouped_by_context() -> None:
    from app.application.analysis_ports import (
        PressureAnalysisReader,
        TemperatureAnalysisReader,
        WaveAnalysisReader,
    )
    for port in (PressureAnalysisReader, TemperatureAnalysisReader, WaveAnalysisReader):
        assert port.__module__ == "app.application.analysis_ports"


def test_sensor_health_ports_are_grouped_by_context() -> None:
    from app.application.sensor_ports import (
        AcousticAltimeterTelemetryGateway,
        AmbientLightTelemetryGateway,
        AirTemperatureTelemetryGateway,
        AtmosphericPressureTelemetryGateway,
        ChlorophyllATelemetryGateway,
        ConductivityTelemetryGateway,
        DissolvedOxygenTelemetryGateway,
        ImuTelemetryGateway,
        ImuTelemetryReader,
        HumidityTelemetryGateway,
        MarineCurrentTelemetryGateway,
        PressureTelemetryGateway,
        PressureTelemetryReader,
        PHTelemetryGateway,
        RainfallTelemetryGateway,
        SalinityTelemetryGateway,
        TemperatureTelemetryGateway,
        TemperatureTelemetryReader,
        TurbidityTelemetryGateway,
        UnderwaterAcousticTelemetryGateway,
        WindTelemetryGateway,
    )

    for port in (
        AcousticAltimeterTelemetryGateway,
        AmbientLightTelemetryGateway,
        AirTemperatureTelemetryGateway,
        AtmosphericPressureTelemetryGateway,
        ChlorophyllATelemetryGateway,
        ConductivityTelemetryGateway,
        DissolvedOxygenTelemetryGateway,
        ImuTelemetryGateway,
        ImuTelemetryReader,
        HumidityTelemetryGateway,
        MarineCurrentTelemetryGateway,
        PressureTelemetryGateway,
        PressureTelemetryReader,
        PHTelemetryGateway,
        RainfallTelemetryGateway,
        SalinityTelemetryGateway,
        TemperatureTelemetryGateway,
        TemperatureTelemetryReader,
        TurbidityTelemetryGateway,
        UnderwaterAcousticTelemetryGateway,
        WindTelemetryGateway,
    ):
        assert port.__module__ == "app.application.sensor_ports"


def test_battery_port_is_grouped_by_context() -> None:
    from app.application.battery_ports import BatteryTelemetryReader

    assert BatteryTelemetryReader.__module__ == "app.application.battery_ports"


def test_quality_summary_port_is_grouped_by_context() -> None:
    from app.application.quality_ports import QualitySummaryReader

    assert QualitySummaryReader.__module__ == "app.application.quality_ports"


def test_temperature_alert_ports_are_grouped_by_context() -> None:
    from app.application.alert_ports import TemperatureAlertsReader, TemperatureAlertStore

    assert TemperatureAlertsReader.__module__ == "app.application.alert_ports"
    assert TemperatureAlertStore.__module__ == "app.application.alert_ports"


def test_sensor_health_ports_are_grouped_by_context() -> None:
    from app.application.sensor_health_ports import (
        SensorHealthCheckGateway,
        SensorHealthCheckWriter,
        SensorHealthReader,
    )

    for port in (SensorHealthCheckGateway, SensorHealthCheckWriter, SensorHealthReader):
        assert port.__module__ == "app.application.sensor_health_ports"


def test_device_ports_are_grouped_by_context() -> None:
    from app.application.device_ports import (
        DeviceHealthReader,
        DeviceListingReader,
        DeviceRegistry,
        DeviceStatusRegistry,
    )

    for port in (
        DeviceHealthReader,
        DeviceListingReader,
        DeviceRegistry,
        DeviceStatusRegistry,
    ):
        assert port.__module__ == "app.application.device_ports"


def test_maintenance_reader_is_grouped_with_maintenance_ports() -> None:
    from app.application.maintenance_ports import MaintenanceReader

    assert MaintenanceReader.__module__ == "app.application.maintenance_ports"


def test_wave_analysis_reader_is_grouped_with_cross_context_analysis_ports() -> None:
    from app.application.analysis_ports import WaveAnalysisReader

    assert WaveAnalysisReader.__module__ == "app.application.analysis_ports"


def test_database_health_reader_is_grouped_with_system_ports() -> None:
    from app.application.system_ports import (
        DatabaseHealthReader as SystemDatabaseHealthReader,
    )

    assert SystemDatabaseHealthReader.__module__ == "app.application.system_ports"


def test_core_sensor_persistence_entities_are_grouped_by_context() -> None:
    from app.sensor_entities import (
        AcousticAltimeterReadingEntity,
        AirTemperatureReadingEntity,
        AmbientLightReadingEntity,
        AtmosphericPressureReadingEntity,
        ChlorophyllAReadingEntity,
        DissolvedOxygenReadingEntity,
        HumidityReadingEntity,
        ImuReadingEntity,
        MarineCurrentReadingEntity,
        PHReadingEntity,
        PressureReadingEntity,
        RainfallReadingEntity,
        SalinityReadingEntity,
        SensorHealthCheckEntity,
        TemperatureReadingEntity,
        TurbidityReadingEntity,
        UnderwaterAcousticReadingEntity,
        ConductivityReadingEntity,
        WindReadingEntity,
    )

    assert AmbientLightReadingEntity.__module__ == "app.sensor_entities"
    assert AcousticAltimeterReadingEntity.__module__ == "app.sensor_entities"
    assert AirTemperatureReadingEntity.__module__ == "app.sensor_entities"
    assert AtmosphericPressureReadingEntity.__module__ == "app.sensor_entities"
    assert ChlorophyllAReadingEntity.__module__ == "app.sensor_entities"
    assert ConductivityReadingEntity.__module__ == "app.sensor_entities"
    assert DissolvedOxygenReadingEntity.__module__ == "app.sensor_entities"
    assert HumidityReadingEntity.__module__ == "app.sensor_entities"
    assert PressureReadingEntity.__module__ == "app.sensor_entities"
    assert RainfallReadingEntity.__module__ == "app.sensor_entities"
    assert SalinityReadingEntity.__module__ == "app.sensor_entities"
    assert SensorHealthCheckEntity.__module__ == "app.sensor_entities"
    assert TemperatureReadingEntity.__module__ == "app.sensor_entities"
    assert TurbidityReadingEntity.__module__ == "app.sensor_entities"
    assert UnderwaterAcousticReadingEntity.__module__ == "app.sensor_entities"
    assert ImuReadingEntity.__module__ == "app.sensor_entities"
    assert MarineCurrentReadingEntity.__module__ == "app.sensor_entities"
    assert PHReadingEntity.__module__ == "app.sensor_entities"
    assert WindReadingEntity.__module__ == "app.sensor_entities"


def test_orm_compatibility_facade_is_removed_and_never_imported() -> None:
    assert not (API_APP / "entities.py").exists()
    for source_root in (
        API_APP,
        API_APP.parent / "tests",
        API_APP.parent / "alembic",
    ):
        for path in source_root.rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            compatibility_imports = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
                and node.module in {"entities", "app.entities"}
            ]
            assert not compatibility_imports, path.relative_to(API_APP.parent)


def test_alembic_registers_context_entities_without_compatibility_facade() -> None:
    migration_env = ast.parse(
        (API_APP.parent / "alembic" / "env.py").read_text(encoding="utf-8")
    )
    imported_contexts = {
        alias.name
        for node in ast.walk(migration_env)
        if isinstance(node, ast.ImportFrom) and node.module == "app"
        for alias in node.names
    }

    assert "entities" not in imported_contexts
    assert imported_contexts.issuperset(
        {
            "alert_entities",
            "fleet_entities",
            "maintenance_entities",
            "sensor_entities",
            "telemetry_entities",
        }
    )


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
    assert isinstance(get_buoy_registrar(session), BuoyRegistryRepository)
    assert isinstance(get_buoy_status_registry(session), BuoyRegistryRepository)
    assert get_buoy_registrar(session).list_buoy_snapshots() == []


def test_legacy_buoy_repository_module_is_removed_and_never_imported() -> None:
    assert not (API_APP / "repository.py").exists()
    production_files = API_APP.rglob("*.py")

    for path in production_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports_legacy_adapter = any(
            isinstance(node, ast.ImportFrom)
            and (
                node.module in {"repository", "app.repository"}
                or any(alias.name == "BuoyRepository" for alias in node.names)
            )
            for node in ast.walk(tree)
        )
        assert not imports_legacy_adapter, path.relative_to(API_APP)


def test_stale_buoy_queries_use_the_fleet_activity_adapter() -> None:
    from app.adapter_dependencies import get_stale_buoy_reader

    assert isinstance(get_stale_buoy_reader(object()), BuoyActivityRepository)


def test_buoy_location_updates_use_the_location_adapter() -> None:
    from app.adapter_dependencies import (
        get_buoy_location_updater,
        get_buoy_location_history_reader,
        get_fleet_location_reader,
        get_movement_analysis_reader,
        get_wave_analysis_reader,
    )

    session = object()
    assert isinstance(get_buoy_location_updater(session), BuoyLocationRepository)
    assert isinstance(get_buoy_location_history_reader(session), BuoyLocationRepository)
    assert isinstance(get_fleet_location_reader(session), BuoyLocationRepository)
    assert isinstance(get_movement_analysis_reader(session), BuoyLocationRepository)
    wave_reader = get_wave_analysis_reader(session)
    assert isinstance(wave_reader, WaveAnalysisRepository)
    assert callable(wave_reader.list_imu)
    assert callable(wave_reader.list_locations)
    assert wave_reader.locations.db is session
    assert wave_reader.imu.db is session


def test_temperature_alert_ports_use_the_composed_alert_adapter() -> None:
    from app.adapter_dependencies import (
        get_temperature_alert_store,
        get_temperature_alerts_reader,
    )

    session = object()
    assert isinstance(get_temperature_alerts_reader(session), TemperatureAlertRepository)
    assert isinstance(get_temperature_alert_store(session), TemperatureAlertRepository)


def test_telemetry_job_http_port_is_implemented_by_sql_adapter() -> None:
    from app.adapter_dependencies import get_telemetry_ingestion_job_repository

    adapter = get_telemetry_ingestion_job_repository(object())

    assert isinstance(adapter, TelemetryIngestionJobStore)
    route_source = (API_APP / "routers" / "ingestion.py").read_text(encoding="utf-8")
    assert "from ..telemetry_ingestion_job_repository import" not in route_source


def test_temperature_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import (
        get_temperature_analysis_reader,
        get_temperature_telemetry_gateway,
    )

    session = object()
    assert isinstance(get_temperature_telemetry_gateway(session), TemperatureRepository)
    assert isinstance(get_temperature_analysis_reader(session), TemperatureRepository)


def test_pressure_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import (
        get_pressure_analysis_reader,
        get_pressure_telemetry_gateway,
    )

    session = object()
    assert isinstance(get_pressure_telemetry_gateway(session), PressureRepository)
    assert isinstance(get_pressure_analysis_reader(session), PressureRepository)


def test_salinity_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_salinity_telemetry_gateway

    session = object()
    assert isinstance(get_salinity_telemetry_gateway(session), SalinityRepository)


def test_imu_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_imu_telemetry_gateway

    session = object()
    assert isinstance(get_imu_telemetry_gateway(session), ImuRepository)


def test_ambient_light_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_ambient_light_telemetry_gateway

    session = object()
    assert isinstance(
        get_ambient_light_telemetry_gateway(session), AmbientLightRepository
    )


def test_wind_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_wind_telemetry_gateway

    session = object()
    assert isinstance(get_wind_telemetry_gateway(session), WindRepository)


def test_marine_current_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_marine_current_telemetry_gateway

    session = object()
    assert isinstance(
        get_marine_current_telemetry_gateway(session), MarineCurrentRepository
    )


def test_turbidity_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_turbidity_telemetry_gateway

    session = object()
    assert isinstance(get_turbidity_telemetry_gateway(session), TurbidityRepository)


def test_dissolved_oxygen_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_dissolved_oxygen_telemetry_gateway

    session = object()
    assert isinstance(
        get_dissolved_oxygen_telemetry_gateway(session), DissolvedOxygenRepository
    )


def test_ph_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_ph_telemetry_gateway

    session = object()
    assert isinstance(get_ph_telemetry_gateway(session), PHRepository)


def test_conductivity_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_conductivity_telemetry_gateway

    session = object()
    assert isinstance(
        get_conductivity_telemetry_gateway(session), ConductivityRepository
    )


def test_chlorophyll_a_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_chlorophyll_a_telemetry_gateway

    session = object()
    assert isinstance(
        get_chlorophyll_a_telemetry_gateway(session), ChlorophyllARepository
    )


def test_rainfall_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_rainfall_telemetry_gateway

    session = object()
    assert isinstance(get_rainfall_telemetry_gateway(session), RainfallRepository)


def test_humidity_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_humidity_telemetry_gateway

    session = object()
    assert isinstance(get_humidity_telemetry_gateway(session), HumidityRepository)


def test_air_temperature_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_air_temperature_telemetry_gateway

    session = object()
    assert isinstance(
        get_air_temperature_telemetry_gateway(session), AirTemperatureRepository
    )


def test_atmospheric_pressure_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_atmospheric_pressure_telemetry_gateway

    session = object()
    assert isinstance(
        get_atmospheric_pressure_telemetry_gateway(session),
        AtmosphericPressureRepository,
    )


def test_acoustic_altimeter_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_acoustic_altimeter_telemetry_gateway

    session = object()
    assert isinstance(
        get_acoustic_altimeter_telemetry_gateway(session),
        AcousticAltimeterRepository,
    )


def test_underwater_acoustic_telemetry_uses_the_dedicated_adapter() -> None:
    from app.adapter_dependencies import get_underwater_acoustic_telemetry_gateway

    session = object()
    assert isinstance(
        get_underwater_acoustic_telemetry_gateway(session),
        UnderwaterAcousticRepository,
    )


def test_battery_telemetry_uses_its_adapter_and_device_composition() -> None:
    from app.adapter_dependencies import get_battery_telemetry_reader

    session = object()
    adapter = get_battery_telemetry_reader(session)
    assert isinstance(adapter, BatteryRepository)
    assert adapter.db is session
    assert isinstance(adapter.devices, DeviceRepository)


def test_sensor_health_ports_use_the_composed_sensor_health_adapter() -> None:
    from app.adapter_dependencies import (
        get_sensor_health_check_gateway,
        get_sensor_health_reader,
    )

    session = object()
    assert isinstance(get_sensor_health_reader(session), SensorHealthRepository)
    assert isinstance(
        get_sensor_health_check_gateway(session), SensorHealthRepository
    )


def test_quality_summary_uses_its_dedicated_repository() -> None:
    from app.adapter_dependencies import get_quality_summary_reader

    session = object()
    assert isinstance(get_quality_summary_reader(session), QualitySummaryRepository)


def test_batch_ingestion_uses_composed_sensor_and_fleet_adapters() -> None:
    from app.adapter_dependencies import get_telemetry_ingestion_gateway

    session = object()
    gateway = get_telemetry_ingestion_gateway(session)
    assert isinstance(gateway, TelemetryIngestionRepository)
    assert isinstance(gateway, TelemetryIngestionGateway)
    assert gateway.locations.db is session
    assert gateway.battery.db is session
    assert gateway.sensors.registry.db is session


def test_maintenance_reader_uses_its_composed_read_adapter() -> None:
    from app.adapter_dependencies import get_maintenance_reader

    session = object()
    reader = get_maintenance_reader(session)
    assert isinstance(reader, MaintenanceRepository)
    assert isinstance(reader, MaintenanceReader)
    assert reader.battery.db is session
    assert reader.locations.db is session
    assert reader.registry.db is session
    assert reader.devices.db is session


def imported_modules(directory: Path) -> set[str]:
    modules = set()
    for source_file in directory.rglob("*.py"):
        package_parts = ["app", *source_file.relative_to(API_APP).parent.parts]
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.level:
                    parent_parts = package_parts[: len(package_parts) - node.level + 1]
                    modules.add(".".join((*parent_parts, *node.module.split("."))))
                else:
                    modules.add(node.module)
            elif isinstance(node, ast.ImportFrom) and node.level:
                parent_parts = package_parts[: len(package_parts) - node.level + 1]
                modules.add(".".join(parent_parts))
    return modules


def imports_package(modules: set[str], package: str) -> bool:
    return any(module == package or module.startswith(f"{package}.") for module in modules)


def test_domain_does_not_depend_on_api_or_persistence_frameworks() -> None:
    modules = imported_modules(API_APP / "domain")

    assert "app.domain.telemetry_types" in modules
    assert not any(
        module == "app"
        or (module.startswith("app.") and not module.startswith("app.domain."))
        for module in modules
    )
    assert not imports_package(modules, "fastapi")
    assert not imports_package(modules, "sqlalchemy")
    assert not imports_package(modules, "pydantic")


def test_application_does_not_depend_on_http_or_database_frameworks() -> None:
    modules = imported_modules(API_APP / "application")

    assert "app.application.ports" not in modules
    assert not (API_APP / "application" / "ports.py").exists()
    assert "app.domain.wave" in modules
    assert not any(
        module == "app"
        or (
            module.startswith("app.")
            and not module.startswith(("app.application.", "app.domain."))
        )
        for module in modules
    )
    assert not imports_package(modules, "fastapi")
    assert not imports_package(modules, "sqlalchemy")
    assert not imports_package(modules, "pydantic")
    assert "os" not in modules


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


def test_device_router_uses_scoped_http_contracts() -> None:
    device_router = ast.parse(
        (API_APP / "routers" / "devices.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module for node in ast.walk(device_router) if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.devices" in imported_modules
    assert "models" not in imported_modules


def test_fleet_router_uses_scoped_http_contracts() -> None:
    buoy_router = ast.parse(
        (API_APP / "routers" / "buoys.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module for node in ast.walk(buoy_router) if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.fleet" in imported_modules
    assert "models" not in imported_modules


def test_quality_router_uses_scoped_http_contracts() -> None:
    quality_router = ast.parse(
        (API_APP / "routers" / "quality.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(quality_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.quality" in imported_modules
    assert "models" not in imported_modules


def test_battery_router_uses_scoped_http_contracts() -> None:
    battery_router = ast.parse(
        (API_APP / "routers" / "battery.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(battery_router)
        if isinstance(node, ast.ImportFrom)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(battery_router)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "schemas.battery" in imported_modules
    assert "models" not in imported_modules
    assert "get_device_snapshot" in called_attributes
    assert "get_device" not in called_attributes


def test_analytics_routers_use_scoped_http_contracts() -> None:
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
    assert "models" not in imported_modules


def test_sensor_router_uses_scoped_http_contracts() -> None:
    sensor_router = ast.parse(
        (API_APP / "routers" / "sensors.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(sensor_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.sensors" in imported_modules
    assert "models" not in imported_modules


def test_maintenance_router_uses_scoped_http_contracts() -> None:
    maintenance_router = ast.parse(
        (API_APP / "routers" / "maintenance.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(maintenance_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.maintenance" in imported_modules
    assert "models" not in imported_modules


def test_ingestion_router_uses_scoped_http_contracts() -> None:
    ingestion_router = ast.parse(
        (API_APP / "routers" / "ingestion.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(ingestion_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.telemetry" in imported_modules
    assert "models" not in imported_modules


def test_core_sensor_http_contracts_use_scoped_schema_modules() -> None:
    sensor_router = ast.parse(
        (API_APP / "routers" / "sensors.py").read_text(encoding="utf-8")
    )
    imported_modules = {
        node.module
        for node in ast.walk(sensor_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.telemetry" in imported_modules
    assert "models" not in imported_modules

    ingestion_router = ast.parse(
        (API_APP / "routers" / "ingestion.py").read_text(encoding="utf-8")
    )
    ingestion_imports = {
        node.module
        for node in ast.walk(ingestion_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.ingestion" in ingestion_imports
    assert "models" not in ingestion_imports

    fleet_router = ast.parse((API_APP / "routers" / "buoys.py").read_text(encoding="utf-8"))
    fleet_imports = {
        node.module
        for node in ast.walk(fleet_router)
        if isinstance(node, ast.ImportFrom)
    }
    assert "schemas.fleet_summary" in fleet_imports
    assert "models" not in fleet_imports


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

    assert isinstance(adapter, BuoySummaryRepository)
    assert isinstance(adapter, BuoySummaryReader)
    assert not hasattr(adapter, "telemetry")
    assert isinstance(adapter.registry, BuoyRegistryRepository)
    assert isinstance(adapter.temperature, TemperatureRepository)
    assert isinstance(adapter.battery, BatteryRepository)


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


def test_http_routers_do_not_import_sqlalchemy() -> None:
    for source_file in (API_APP / "routers").glob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert not any(module == "sqlalchemy" or module.startswith("sqlalchemy.") for module in modules), (
            f"{source_file.name} must translate persistence errors outside the HTTP adapter"
        )


def test_telemetry_router_uses_unit_of_work_port_for_transactions() -> None:
    tree = ast.parse((API_APP / "routers" / "ingestion.py").read_text(encoding="utf-8"))
    infrastructure_attributes = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr in {"db", "info", "commit", "rollback"}
    }

    assert not infrastructure_attributes


def test_telemetry_worker_does_not_depend_on_http_router() -> None:
    tree = ast.parse(
        (API_APP / "telemetry_job_worker.py").read_text(encoding="utf-8")
    )
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert not any(module.endswith("routers.ingestion") for module in imported)


def test_telemetry_batch_processor_is_independent_of_http_frameworks() -> None:
    tree = ast.parse(
        (API_APP / "application" / "telemetry_batch_ingestion.py").read_text(
            encoding="utf-8"
        )
    )
    modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }

    assert not imports_package(modules, "fastapi")
    assert not imports_package(modules, "starlette")
    assert not imports_package(modules, "prometheus_client")
    assert not imports_package(modules, "pydantic")
    assert not imports_package(modules, "schemas")
    assert not any(
        isinstance(node, ast.Attribute) and node.attr == "model_dump"
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.level > 0
        and node.module == "metrics"
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.ImportFrom)
        and node.level > 0
        and node.module is not None
        and node.module.startswith("routers")
        for node in ast.walk(tree)
    )


def test_prometheus_telemetry_metrics_resolves_registered_instruments() -> None:
    from app.prometheus_telemetry_metrics import PrometheusTelemetryMetrics

    metrics = PrometheusTelemetryMetrics()
    processor_tree = ast.parse(
        (API_APP / "application" / "telemetry_batch_ingestion.py").read_text(
            encoding="utf-8"
        )
    )
    metric_names = {
        node.args[0].value
        for node in ast.walk(processor_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "metric"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    }
    assert metric_names
    for metric_name in metric_names:
        assert metrics.metric(metric_name) is not None

    try:
        metrics.metric("missing_telemetry_metric")
    except KeyError as error:
        assert "Unknown telemetry metric" in str(error)
    else:
        raise AssertionError("Unknown metrics must fail clearly")


def test_quality_router_depends_on_sensor_port_not_repository_adapter() -> None:
    tree = ast.parse((API_APP / "routers" / "quality.py").read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "repository" not in imported_modules
    assert "application.quality_ports" in imported_modules


def test_fleet_telemetry_router_depends_on_application_port_not_repository_adapter() -> None:
    tree = ast.parse((API_APP / "routers" / "telemetry.py").read_text(encoding="utf-8"))
    imported_modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }

    assert "repository" not in imported_modules
    assert "application.fleet_ports" in imported_modules


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
