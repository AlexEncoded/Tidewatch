from contextlib import asynccontextmanager
import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .telemetry import configure_telemetry
from .metrics import http_request_duration_seconds, http_requests_total
from .application.wave_analysis import configured_wave_imu_factor
from .routers.devices import router as devices_router
from .routers.buoys import router as buoys_router
from .routers.telemetry import router as telemetry_router
from .routers.ingestion import router as ingestion_router
from .routers.analytics import router as analytics_router
from .routers.battery import router as battery_router
from .routers.quality import router as quality_router
from .routers.alerts import router as alerts_router
from .routers.sensors import router as sensors_router
from .routers.maintenance import router as maintenance_router
from .routers.system import router as system_router


logger = logging.getLogger("tidewatch.api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="Tidewatch API",
    description="API for monitoring autonomous ocean buoys.",
    version="0.2.0",
    lifespan=lifespan,
)
app.state.otel_enabled = configure_telemetry(app)
app.include_router(devices_router)
app.include_router(buoys_router)
app.include_router(telemetry_router)
app.include_router(ingestion_router)
app.include_router(analytics_router)
app.include_router(battery_router)
app.include_router(quality_router)
app.include_router(alerts_router)
app.include_router(sensors_router)
app.include_router(maintenance_router)
app.include_router(system_router)


@app.middleware("http")
async def request_logging_middleware(request, call_next):
    started_at = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    http_requests_total.labels(
        method=request.method, status_code=str(response.status_code)
    ).inc()
    http_request_duration_seconds.labels(method=request.method).observe(duration_ms / 1000)
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
