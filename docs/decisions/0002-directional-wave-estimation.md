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

## Decisión

No publicar una dirección de oleaje derivada de las señales actuales. Mantener
el resultado limitado a altura y período, identificados como experimentales.
Antes de habilitar dirección, definir e implementar una de estas entradas
observables y sincronizadas:

- GNSS tridimensional de alta frecuencia con desplazamientos horizontales y
  verticales de calidad documentada; o
- heave y desplazamientos/aceleraciones horizontales con pitch, roll y heading
  referidos a un marco de coordenadas conocido.

La estimación deberá especificar orientación (desde/hacia y referencia norte),
tratamiento de gaps y calidad, y método espectral. No se aceptará solamente una
dirección media de movimiento de la boya como dirección de ola.

## Criterios de validación

- Tests deterministas para orientación, sincronización, gaps, calidad y señales
  sin energía direccional suficiente.
- Casos sintéticos para comprobar el cálculo y sus límites; no cuentan como
  validación física.
- Comparación de campo con una boya direccional de referencia en condiciones
  representativas antes de etiquetar el resultado como operativo.
- Respuesta API y métricas distinguen falta de datos y desacuerdo entre fuentes
  sin inventar un ángulo.

## Consecuencias

El contrato de API no promete dirección de ola hasta que se cumplan esos
requisitos. La estimación de altura y período existente permanece independiente
y continúa marcada como experimental.
