# Ideas y backlog

## Ideas sueltas

- Dashboard de despliegues.
- Entornos efímeros por pull request.
- Despliegues canary y blue/green.
- DORA metrics.
- Simulación de incidentes.
- Backups y restauración automatizada.
- ChatOps para consultar el estado del sistema.
- Tests de carga y chaos engineering.
- Usar el historial de telemetría para entrenar un modelo de predicción.
- Procesar continuamente las nuevas lecturas de las boyas.
- Escalar temporalmente capacidad de cómputo con GPUs en Azure.
- Distribuir la carga de datos recientes entre workers.
- Simular un modelo de ML para practicar el flujo completo sin depender de un
  modelo real.
- Equipar cada boya con dos sistemas de sensores para validar lecturas y avisar
  a mantenimiento cuando exista una divergencia.
- Convertir las boyas en “turbomegaboyas” con una suite ampliada de sensores.

## Suite futura de sensores — turbomegaboyas

La lista completa queda aprobada como objetivo de largo plazo. Se incorporará
poco a poco, priorizando primero el valor operativo y el consumo energético.
Todos los sensores críticos deberán contemplar autodiagnóstico y, cuando el
coste y el consumo lo permitan, canales duplicados A/B para detectar fallos.

## Principio obligatorio: arquitectura dual de cada boya

La redundancia no será únicamente lógica ni estará limitada a algunos
sensores. Cada boya estará compuesta por **dos dispositivos físicos idénticos**
(A y B), y cada dispositivo tendrá:

- Su propia batería y medición de estado energético.
- Su propia unidad de procesamiento y comunicaciones.
- Su propia suite completa de sensores.
- Su propio reloj, identificador de unidad y estado de salud.

La boya seguirá operativa si una unidad falla. El sistema comparará las
lecturas A/B dentro de márgenes aceptables por familia de sensor:

```text
lectura A + lectura B
          ↓
 comparación y validación
          ↓
 dato fiable / incongruente / unidad degradada
          ↓
 telemetría + mantenimiento + observabilidad
```

Cuando exista divergencia, se conservarán ambas lecturas y se marcará el dato
como `suspect` o `invalid` según la gravedad. La plataforma seguirá mostrando
la lectura disponible, pero no la usará en análisis sensibles si no supera las
reglas de calidad. Mantenimiento recibirá la unidad sospechosa, la familia de
sensor, la diferencia observada y la última lectura válida conocida.

La disponibilidad objetivo de la boya será **99,99%**, entendida como
continuidad operativa gracias a la unidad gemela y no como garantía de que cada
sensor individual sea infalible. El diseño deberá contemplar también fallos
de batería, comunicaciones, reloj, almacenamiento y procesador, además de
fallos de sensores.

### Prioridad operativa

- **IMU (acelerómetro y giroscopio):** inclinación, golpes, balanceo, vibración
  y movimiento de la boya.
- **Luz ambiental:** distinguir día/noche, nubosidad intensa y tormentas.
- **Anemómetro y veleta:** velocidad y dirección del viento.
- **Sensor de corriente marina:** dirección y velocidad de corrientes.
- **Turbidez:** sedimentos, contaminación, escorrentías y floraciones.

### Prioridad oceanográfica y ambiental

- **Oxígeno disuelto:** salud del ecosistema y episodios de hipoxia.
- **pH y conductividad:** cambios químicos, acidificación y contaminación.
- **Clorofila-a:** actividad biológica y floraciones de algas.
- **Sensor meteorológico:** presión atmosférica, humedad, temperatura del aire
  y lluvia.

### Sensores avanzados

- **Altímetro acústico:** profundidad del fondo o distancia a la superficie.
- **GNSS/IMU avanzado:** altura, periodo y dirección de ola experimental.
- **Sensor acústico submarino:** corrientes, fauna o embarcaciones en fases
  futuras, sujeto a alcance, privacidad y consumo.

El altímetro no sustituirá inicialmente a la presión y la IMU: para una boya
flotante, la combinación de ambas ofrece una ruta más robusta para estimar
oleaje. Cada nuevo sensor deberá incluir rango válido, frecuencia de muestreo,
calibración, coste energético, almacenamiento, métrica Prometheus, panel
Grafana, alerta de mantenimiento y estrategia de datos duplicados.

## Backlog inicial

- [ ] Elegir la aplicación de negocio.
- [ ] Definir el MVP.
- [ ] Elegir stack tecnológico.
- [ ] Crear el primer pipeline.
- [ ] Diseñar los entornos.

## Futuro: predicción de condiciones marítimas

Cuando Tidewatch tenga suficiente histórico de temperaturas y otras señales,
añadiremos un flujo experimental de análisis y predicción. No forma parte del
MVP ni se debe empezar todavía.

### Objetivo

Enviar ventanas recientes de datos de las boyas a un modelo simulado que
analice la serie temporal y produzca predicciones o avisos operativos.

### Flujo previsto

```text
Boyas → ingesta continua → almacenamiento histórico
          ↓
     ventana reciente
          ↓
   cola / stream de trabajo
          ↓
 workers escalables en Azure
          ↓
 GPU temporal para inferencia o entrenamiento
          ↓
 predicciones → API → dashboard y alertas
```

### Qué queremos practicar

- Ventanas temporales y características de series temporales.
- Procesamiento continuo de nueva información.
- Distribución de trabajos entre workers.
- Escalado bajo demanda de recursos con GPU.
- Terraform para provisionar y destruir capacidad de cómputo.
- Observabilidad del pipeline de datos y del modelo.
- Versionado de datos, modelos y predicciones.
- Costes, límites y apagado automático de recursos Azure.

### Restricciones iniciales

- El modelo será simulado; no se busca precisión científica.
- No se utilizarán GPUs hasta tener un histórico suficiente.
- Primero construiremos el flujo de datos con CPU y datos sintéticos.
- La predicción será informativa y no tomará decisiones críticas.

## Evolución arquitectónica: DDD ligero y monolito modular

La API evolucionará poco a poco desde su estructura actual hacia un monolito
modular inspirado en DDD y con separación hexagonal cuando aporte valor. Los
primeros módulos previstos son:

Este objetivo queda formalizado en el roadmap como adopción progresiva de
arquitectura hexagonal con DDD ligero: primero límites y contratos, después
casos de uso y puertos/adaptadores, sin extraer microservicios prematuramente.

- `fleet`: boyas, ubicación y estado operativo.
- `telemetry`: ingesta y lecturas.
- `sensors`: canales A/B, calidad y diagnóstico.
- `maintenance`: incidencias y alertas.
- `analytics`: oleaje, deriva y predicciones futuras.

La prioridad será establecer límites claros, casos de uso y contratos internos
sin introducir ceremonias innecesarias. La extracción posterior a servicios
independientes solo se hará cuando el dominio, el escalado o la operación lo
justifiquen.
