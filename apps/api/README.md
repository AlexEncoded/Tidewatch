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

Documentación interactiva: <http://localhost:8000/docs>

## Endpoints iniciales

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/buoys` | Registrar una boya |
| `GET` | `/api/v1/buoys` | Listar boyas y última temperatura |
| `POST` | `/api/v1/buoys/{id}/temperatures` | Registrar temperatura |
| `GET` | `/api/v1/buoys/{id}/temperatures` | Consultar historial |

Las lecturas aceptan temperaturas entre `-5 °C` y `45 °C`. Las boyas y lecturas
se persisten en PostgreSQL cuando se ejecuta mediante Docker Compose.

## Tests

```bash
pytest
```
