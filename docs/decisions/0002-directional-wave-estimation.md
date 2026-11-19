# ADR-0002: Requisitos para estimar la dirección del oleaje

- Estado: aceptada
- Fecha: 2026-11-18

## Contexto

El análisis experimental actual combina el rango vertical de GNSS y la
aceleración vertical de la IMU para estimar altura y período. La respuesta no
incluye dirección. Las posiciones disponibles guardan latitud, longitud y
altitud, y la IMU guarda aceleración y velocidad angular; no hay contrato que
garantice heading/azimut calibrado, actitud de pitch/roll, frecuencia adecuada
ni sincronización con precisión suficiente para una estimación direccional.

La documentación de NDBC/NOAA describe que sus mediciones direccionales usan
movimiento vertical junto con azimut, pitch y roll, y obtienen información de
dirección de relaciones espectrales entre movimiento de la boya y sus ejes
horizontal/vertical ([FAQ de NDBC](https://www.ndbc.noaa.gov/faq/wave.shtml),
[procedimientos de análisis](https://www.ndbc.noaa.gov/wavemeas.pdf)).

La configuración actual tampoco es una fuente válida para validar esa
capacidad: el simulador envía una muestra cada 10 segundos por defecto para una
onda sintética de 30 segundos y genera coordenadas horizontales con offsets
aleatorios de hasta 0,00002° (aproximadamente 2,2 m norte/sur y 1,8 m este/oeste
a la latitud simulada). Esa variación no representa el desplazamiento horizontal
de una boya causado por el oleaje.

El simulador ofrece ahora un modo opt-in (`--wave-direction-degrees`) que
genera una propagación sintética hacia un rumbo conocido, sincroniza la
velocidad horizontal con la elevación y requiere un intervalo máximo de 3
segundos. Sirve para preparar y probar entradas del futuro cálculo; no añade
una estimación direccional al API ni cuenta como validación científica.

## Decisión

No publicar una dirección de oleaje derivada de las señales actuales. Mantener
el resultado limitado a altura y período, identificados como experimentales.
Antes de habilitar dirección, definir e implementar una de estas entradas
observables y sincronizadas:

- GNSS de alta frecuencia con velocidad instantánea en ejes este, norte y arriba
  (preferiblemente salida Doppler del receptor), cadencia y calidad documentadas; o
- heave y desplazamientos/aceleraciones horizontales con pitch, roll y heading
  referidos a un marco de coordenadas conocido.

La API y la persistencia aceptan ahora los tres componentes de velocidad como
campos opcionales, y el simulador direccional los deriva de su trayectoria
sintética. Esto prepara el contrato y permite comprobar el transporte de datos;
no demuestra que la velocidad GNSS real tenga la resolución, frecuencia ni
calidad necesarias.

Se añadió un prototipo offline `wave_direction_experiment.py` basado en
espectros de elevación y velocidades horizontales GNSS (`eta/u/v`). Calcula la
dirección media del primer momento en la frecuencia de máxima energía de
elevación, con Welch y sin interpolar huecos. No reconstruye el espectro
direccional completo, no está conectado a la API y solo se ha probado con ondas
sintéticas. El umbral de concentración es heurístico, no un criterio de calidad
validado.

La estimación deberá especificar orientación (desde/hacia y referencia norte),
tratamiento de gaps y calidad, y método espectral. No se aceptará solamente una
dirección media de movimiento de la boya como dirección de ola.

## Criterios de validación

- Tests deterministas para orientación, sincronización, gaps, calidad y señales
  sin energía direccional suficiente.
- Casos sintéticos para comprobar el cálculo y sus límites; no cuentan como
  validación física.
- La simulación direccional deberá generar series sincronizadas con resolución
  temporal suficiente y desplazamientos horizontales derivados de una
  propagación definida, sin reutilizar jitter de posición aleatorio como señal.
- Comparación de campo con una boya direccional de referencia en condiciones
  representativas antes de etiquetar el resultado como operativo.
- Respuesta API y métricas distinguen falta de datos y desacuerdo entre fuentes
  sin inventar un ángulo.

## Consecuencias

El contrato de API no promete dirección de ola hasta que se cumplan esos
requisitos. La estimación de altura y período existente permanece independiente
y continúa marcada como experimental.
