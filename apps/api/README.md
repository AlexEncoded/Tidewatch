# Tidewatch API

Primer servicio de Tidewatch. Esta iteración permite registrar boyas y medir la
temperatura del mar.

## Ejecutar localmente

```bash
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1       # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Documentación interactiva: <http://localhost:8000/docs>

## Endpoints iniciales

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/buoys` | Registrar una boya |
| `GET` | `/api/v1/buoys` | Listar boyas y última temperatura |
| `POST` | `/api/v1/buoys/{id}/temperatures` | Registrar temperatura |
| `GET` | `/api/v1/buoys/{id}/temperatures` | Consultar historial |

Las lecturas aceptan temperaturas entre `-5 °C` y `45 °C`. La persistencia en
memoria es intencionada en el MVP; PostgreSQL será la siguiente evolución.

## Tests

```bash
pytest
```
