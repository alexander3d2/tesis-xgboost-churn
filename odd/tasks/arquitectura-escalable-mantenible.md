# Arquitectura escalable y mantenible

## Objetivo
Reducir acoplamiento y mejorar mantenibilidad sin cambiar el contrato provisional de la API ni mezclar datos reales con fixtures sintéticos.

## Alcance autorizado
- Añadir puertos `Protocol` para las dependencias del constructor de datasets.
- Añadir una fachada compatible para adaptadores CSV.
- Introducir un servicio pequeño para el listado de scores.
- Actualizar el README con capas, fronteras de datos y verificación.
- Mantener intactos los contratos HTTP actuales y los adaptadores existentes.

## Fuera de alcance
- No acceder a Datasheet, CSV reales, bases de datos reales ni red.
- No implementar persistencia de scores, autenticación ni reglas de negocio.
- No reorganizar `core/model.py` ni convertir el prototipo en microservicios.

## Tareas
- [x] A1 — Desacoplar `TrainingExampleBuilder` mediante puertos y conservar compatibilidad CSV.
- [x] A2 — Introducir `RiskScoreService` y enrutar el listado provisional mediante dependencia explícita.
- [x] A3 — Documentar estructura, fronteras de datos y verificación local.
- [ ] A4 — Ejecutar pruebas, revisar diff y cerrar cada unidad con commit convencional.

## Verificación
- Pruebas focalizadas de training y API.
- Suite Python completa y `pip check`.
- Confirmar que no se modifican contratos HTTP ni archivos locales no relacionados.
