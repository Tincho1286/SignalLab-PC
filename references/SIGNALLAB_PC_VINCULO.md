# SignalLab: calculadora y PC

## Separación de trabajo

Este proyecto y su chat se mantienen para HP Prime. La migración a Python para PC se desarrolla en un chat y una carpeta separados, con objetivo de equivalencia funcional completa, no una sustitución del programa HP PPL.

## Referencia canónica de HP Prime

- Carpeta del proyecto HP: `C:/Users/lesca/Documents/Software_Apps/SignalLab Hp Prime`.
- Fuente: `C:/Users/lesca/Documents/Software_Apps/SignalLab Hp Prime/SignalLab_5.0/SignalLab_App_5.0.hppl`.
- Versión: SignalLab 5.0, revisión de fórmulas del 21/10/2026.
- SHA256 de la fuente (bytes del archivo): `9EC7E69183AC50303A4EF0FDFAFD4B585F33D75D2164AE725E95574A75033DCB`.
- La copia congelada con el mismo hash está en `references/SignalLab_App_5.0.hppl` dentro del proyecto PC.
- Guía: `SignalLab_5.0/GUIA_SignalLab_5.0.md`.
- Alcance y comprobaciones previas: `SignalLab_5.0/NOTAS_REVISION.md`, `SignalLab_5.0/PRUEBAS.md`, `Herramientas_desarrollo/verificar_*.py`.
- Los PDF/Word incluidos son anteriores a las últimas adendas. El código y la guía Markdown son las referencias más recientes.

## Contrato de vinculación

1. PC conserva una copia de referencia identificada por hash y un inventario de funciones/menús HP → implementación Python → pruebas → estado. No se presenta una pantalla vacía o una función pendiente como migrada.
2. El proyecto PC lee este proyecto como referencia; no modifica HPPL, paquetes instalables ni documentación de calculadora. Este chat no modifica archivos de PC de forma implícita.
3. Las correcciones transferibles se registran con entrada, resultado esperado, convención matemática y estado en cada plataforma. No se traslada un defecto conocido solo para reproducirlo.
4. Cualquier actualización del origen requiere comparar versiones y revisar diferencias; no hay sobrescritura ni sincronización automática de códigos distintos.
5. El banco/intercambio de señales de PC debe conservar muestras complejas, eje, origen, paso, unidades y metadatos. La compatibilidad con listas/tablas exportadas desde Prime debe ser explícita, sin prometer conexión directa a su hardware.
6. Mantener separadas las expresiones exactas, aproximaciones numéricas y limpieza visual; conservar índices discretos enteros, convenciones de Fourier y datos originales. El CAS de Python no se supone idéntico al CAS HP.

## Inicio

Chat creado: **SignalLab PC — migración Python**.

- Carpeta canónica PC: `C:/Users/lesca/Documents/Software_Apps/SignalLab PC`.
- Carpeta de salida asignada originalmente por Codex: `C:/Users/lesca/Documents/Codex/2026-10-21/signallab-pc/outputs` (copia de trabajo inicial).
- Allí se inventariará el código completo, se establecerá la arquitectura y se implementará una primera aplicación ejecutable con UI y pruebas, dejando trazable todo lo pendiente para alcanzar la paridad completa.
- Este vínculo no implica que la migración esté terminada: su progreso se consulta en el nuevo chat y su matriz de paridad.
