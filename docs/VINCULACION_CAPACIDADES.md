# Vinculación de capacidades HP ↔ PC — esquema 1

## Para qué sirve

Conserva un vocabulario común de herramientas, convenciones matemáticas y casos de cálculo para revisar mejoras en ambas direcciones. La carpeta canónica HP se lee como referencia. No se sobrescriben código HPPL, paquetes ni documentos HP. El mecanismo compara datos y produce un informe; una relación de familia no declara que todas las opciones de una herramienta estén migradas.

## Archivos

- `signallab_pc/assets/capabilities-pc.json`: catálogo de las rutas PC reales y el inventario de llamadas SSMenu de la referencia HP.
- `signallab_pc/assets/reference-cases.json`: entradas, resultados esperados, tolerancias y derivaciones de cinco casos transferibles.
- `docs/INVENTARIO_REPRODUCIBLE_HP.md`: inventario legible con líneas, opciones calculadas y rutas relacionadas.
- `work/reference-case-results.json`: ejecución PC de esos cinco casos, vinculada por hash al catálogo exacto.
- `work/capability-live-comparison.json`: comparación de la referencia congelada con el código HP canónico actual.
- `tests/test_capabilities.py`: extracción, comparación en ambos sentidos, integridad, cambios de contratos y ejecución restringida de casos.

## Identidad y estados

Los identificadores `tool.<familia>.<acción>` se mantienen al cambiar sólo los títulos visibles. No reutilizar un ID para un significado diferente. El campo `platform` identifica quién publica el manifiesto (`pc` o `hp`); una capacidad compartida conserva su ID en ambos. Una función exclusiva usa un ID nuevo. El esquema admite manifiestos HP del mismo formato, pero no fabrica estados de implementación ni resultados de pruebas HP.

Los IDs de menús HP combinan función contenedora, título y ordinal entre llamadas iguales. Los IDs de opciones incluyen posición: reordenar o renombrar obliga a revisar el cambio, y puede requerir correspondencia manual. Las líneas son ubicaciones de evidencia, no identidades. Los títulos o listas construidos en ejecución se conservan como expresiones; no se evalúan. El escaneo no sustituye el análisis del tablero, las ramas ni el comportamiento CAS.

`partial_unreviewed_parity` indica una ruta PC disponible con equivalencia HP pendiente. `pc_extension` distingue los modelos de estados. Todos los menús conservan `unreviewed` hasta una auditoría por opción. Un contador o una prueba puntual no cambia esos estados.

## Flujo de trabajo

1. Exportar el catálogo antes de cambiar una plataforma y conservarlo.
2. Implementar el cambio y registrar la convención y un caso reproducible, con la plataforma aún no probada marcada `not_run`.
3. Exportar después y comparar. Examinar capacidades añadidas/retiradas/modificadas, convenciones, menús y casos. Cualquier cambio del hash HP requiere revisión, incluso si las llamadas de menú son idénticas.
4. Llevar la mejora a la otra plataforma cuando corresponda y ejecutar allí el mismo caso, adaptando sus datos a HP PPL sin alterar su significado.
5. Conservar las evidencias por plataforma. La herramienta no sincroniza programas ni promueve automáticamente una equivalencia.

## Comandos para desarrollo

Desde la carpeta SignalLab PC, con el entorno Python del proyecto:

```powershell
.\.venv\Scripts\python.exe -B -m signallab_pc.capabilities export --hp-source references/SignalLab_App_5.0.hppl --output work/catalogo-nuevo.json
.\.venv\Scripts\python.exe -B -m signallab_pc.capabilities compare work/catalogo-anterior.json work/catalogo-nuevo.json --output work/diferencias.json
.\.venv\Scripts\python.exe -B -m signallab_pc.capabilities check-reference signallab_pc/assets/capabilities-pc.json "C:\Users\lesca\Documents\Software_Apps\SignalLab Hp Prime\SignalLab_5.0\SignalLab_App_5.0.hppl"
.\.venv\Scripts\python.exe -B -m signallab_pc.reference_cases signallab_pc/assets/reference-cases.json --output work/resultados-casos.json
```

El ejecutor sólo admite las operaciones enumeradas en su código; no ejecuta expresiones Python recibidas en JSON. Las comparaciones no modifican los catálogos. La salida de `check-reference` devuelve código 2 ante una referencia distinta; un cambio no se acepta automáticamente.

## Verificación y alcance de la entrega

113 pruebas aprobadas. Cinco casos aprobados en PC y no ejecutados en HP. Se comprobó que el hash HP vigente coincide con la referencia congelada. El paquete Python toma ahora su versión de una única fuente; las rutas de menú están separadas de Qt para poder auditar el catálogo sin abrir ventanas.

Esta entrega actualiza el código y las herramientas de vinculación. No genera otro EXE: el portable entregado sigue siendo 0.10. Falta auditar cada opción y completar las funciones pendientes de la matriz general.
