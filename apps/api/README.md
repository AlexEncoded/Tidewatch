# Tidewatch API

Primer servicio de Tidewatch. Esta iteración permite registrar boyas y medir la
temperatura del mar.

## Ejecutar localmente con PostgreSQL

Desde la raíz del repositorio:

```bash
docker compose up --build
```

La API estará disponible en <http://localhost:8000> y PostgreSQL en el puerto
`5432`.

## Ejecutar solo la API

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1       # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Por defecto, la ejecución local usa SQLite (`tidewatch.db`). Para conectar a
PostgreSQL, define `DATABASE_URL` usando el formato de `.env.example`.

Las migraciones del esquema se ejecutan con:

```bash
alembic upgrade head
```

El contenedor de la API ejecuta este comando automáticamente antes de arrancar.

Documentación interactiva: <http://localhost:8000/docs>

## Endpoints iniciales

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/buoys` | Registrar una boya |
| `GET` | `/api/v1/buoys` | Listar boyas y última temperatura |
| `POST` | `/api/v1/buoys/{id}/temperatures` | Registrar temperatura |
| `GET` | `/api/v1/buoys/{id}/temperatures` | Consultar historial |
| `GET` | `/api/v1/buoys/{id}/temperature-analysis` | Analizar anomalías |
| `GET` | `/api/v1/alerts/temperature` | Listar alertas de temperatura |

Las lecturas aceptan temperaturas entre `-5 °C` y `45 °C`. Las boyas y lecturas
se persisten en PostgreSQL cuando se ejecuta mediante Docker Compose.

El análisis compara la lectura más reciente con la media de la ventana
solicitada, calcula el cambio entre la primera y la última lectura e identifica
la tendencia como `rising`, `falling` o `stable`. Para marcar anomalías necesita
al menos tres lecturas. El umbral por defecto es `2 °C` y se puede ajustar con
`threshold`.

Las alertas se calculan bajo demanda y todavía no se persisten. Más adelante
podrán tener ciclo de vida (`open`, `acknowledged`, `resolved`) y conectarse con
notificaciones o Azure Monitor.

## Tests

```bash
pytest
```
