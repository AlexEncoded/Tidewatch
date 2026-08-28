# Estrategia de idiomas de la documentación

## Objetivo futuro

Adoptar el inglés como idioma por defecto de la documentación pública y
técnica de Tidewatch, manteniendo el español actual como idioma secundario.

## Criterios

- La nueva documentación se redactará primero en inglés.
- El español se conservará como traducción secundaria mientras siga siendo útil
  para el aprendizaje y la colaboración actual.
- Las traducciones deberán mantener los mismos ejemplos, rutas, nombres de
  métricas y decisiones técnicas.
- El código, identificadores, commits y contratos API seguirán usando nombres
  técnicos en inglés.
- La migración será progresiva; no se traducirá documentación estable de forma
  masiva hasta definir una convención de nombres y enlaces entre idiomas.

## Secuencia propuesta

1. Definir nombres canónicos en inglés para los documentos nuevos.
2. Añadir versiones inglesas de `README`, guías operativas y decisiones clave.
3. Mantener el español como versión secundaria enlazada desde cada documento.
4. Actualizar CI o una comprobación documental cuando el volumen justifique
   detectar enlaces o traducciones desincronizadas.
