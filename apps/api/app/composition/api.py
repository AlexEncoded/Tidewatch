"""FastAPI application composition root."""

from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from ..adapters.opentelemetry.tracing import configure_telemetry
from ..adapters.postgres.database import SessionLocal
from ..adapters.prometheus.availability_metrics import initialize_availability_metrics
from ..adapters.prometheus.fleet_metrics import PrometheusFleetMetrics
from ..adapters.prometheus.http_request_metrics import PrometheusHttpRequestMetrics
from ..routers.alerts import router as alerts_router
from ..routers.analytics import router as analytics_router
from ..routers.battery import router as battery_router
from ..routers.buoys import router as buoys_router
from ..routers.devices import router as devices_router
from ..routers.ingestion import router as ingestion_router
from ..routers.maintenance import router as maintenance_router
from ..routers.quality import router as quality_router
from ..routers.sensors import router as sensors_router
from ..routers.system import router as system_router
from ..routers.telemetry import router as telemetry_router


logger = logging.getLogger("tidewatch.api")


def create_app() -> FastAPI:
    """Create the API and compose its HTTP, startup, and observability adapters."""
    http_request_metrics = PrometheusHttpRequestMetrics()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            with SessionLocal() as session:
                initialize_availability_metrics(session, PrometheusFleetMetrics())
        except SQLAlchemyError:
            logger.exception("availability_metrics_initialization_failed")
        yield

    app = FastAPI(
        title="Tidewatch API",
        description="API for monitoring autonomous ocean buoys.",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.state.otel_enabled = configure_telemetry(app)
    for router in (
        devices_router,
        buoys_router,
        telemetry_router,
        ingestion_router,
        analytics_router,
        battery_router,
        quality_router,
        alerts_router,
        sensors_router,
        maintenance_router,
        system_router,
    ):
        app.include_router(router)

    @app.middleware("http")
    async def request_logging_middleware(request, call_next):
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        http_request_metrics.record_request(
            request.method, response.status_code, duration_ms / 1000
        )
        logger.info(
            "http_request method=%s path=%s status_code=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8080"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["*"],
    )
    return app
