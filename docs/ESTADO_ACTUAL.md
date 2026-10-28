> Actualización UI: versión 0.3 con tema oscuro y navegación por tareas. Ver docs/UI_0_3.md. La migración funcional continúa en desarrollo.

# Corrección visual vigente: 0.2.1

Se corrigió el aplastamiento de los formularios reportado por el usuario. Detalles y alcance de revisión visual en UI_0_2_1.md. Ejecutable nuevo: outputs/SignalLab-PC-0.2.1-dev.exe. El alcance matemático de la migración no cambia respecto de 0.2.

# Estado vigente: 0.2 en desarrollo

La primera versión quedó preservada en releases/v0.1.0 con EXE, código y manifest de integridad. El alcance actual y los pendientes se detallan en VERSION_0_2.md. Las notas siguientes son históricas; las incorporaciones de 0.2 no tienen pruebas ejecutadas.

# Estado de continuidad — 21/10/2026

Objetivo vigente: un EXE Windows portable con **todas** las capacidades de la versión HP Prime actual. Una compilación que arranque o una suite parcial no prueba paridad completa. El objetivo sigue activo.

## Ubicaciones

- PC: C:/Users/lesca/Documents/Software_Apps/SignalLab PC.
- HP de referencia: carpeta hermana SignalLab Hp Prime, versión SignalLab_5.0.
- Fuente congelada: references/SignalLab_App_5.0.hppl; contrastar cambios con el proyecto HP antes de nuevos lotes.

## Entorno y evidencia real

- Python 3.12.10 oficial, distribución NuGet, extraída en work/python-nuget; entorno .venv operativo.
- NumPy, SciPy, SymPy, Matplotlib y PySide6 instalados. requirements-lock.txt registra versiones efectivas, incluido PyInstaller.
- 33 pruebas pasaron el 21/10/2026: tests de flujo, operaciones, filtros y UI Qt sin pantalla.
- Las pruebas UI verifican llegada del resultado al hilo gráfico, diseño FIR seguido de respuesta al impulso y edición de una fila de la segunda página.
- El EXE de desarrollo usa main.py y --self-check RUTA_JSON. Ese diagnóstico comprueba dependencias y un flujo acotado; no declara migración terminada.

## Trabajo de este lote

- Se corrigió el inicio del soporte reflejado en par/impar (fallaba incluso en algunos soportes centrados).
- JSON conserva índices enteros mayores que 2^53 sin convertirlos a float.
- filters.py: FIR sin normalizar ganancia (convención HP), cuatro biquads con pasabanda de pico Q, RC, bilineal, ecuaciones en diferencias, impulso/escalón digital, respuesta compleja, polos/ceros y estabilidad.
- systems_panel.py conecta esos cálculos con los módulos Filtros y LTI: edición b/a, diseño, gráficas, aplicación a señal y guardado/carga del filtro.
- Los callbacks de cálculo se reciben explícitamente en el hilo gráfico; sólo se permite un cálculo a la vez para evitar reservas de memoria simultáneas.

## Pendientes para la paridad (no omitir)

1. Completar generadores, tramos, señales especiales y estados N/D/infinito; energía/potencia global y teoría.
2. LTI continuo, correlaciones auto/circular/periódica/normalizada y convolución circular.
3. Laplace/Z/EDO simbólicas, ROC y evaluación de expresiones seguras.
4. Series Fourier continuas/discretas, CTFT/ICTFT, DTFT, comparación DFT/DTFT, espectros, retardo y PSD/Welch calibrada.
5. Muestreo, aliasing, remuestreo y reconstrucción, cuantización/SNR y punto fijo.
6. Completar filtros: RC a partir de frecuencia y componente conocido; edición gráfica de polos/ceros; teoría y estructuras.
7. Control: segundo orden, Bode, realimentación y lugar de raíces.
8. Teoría HP completa, historial persistente, mediciones de cursor, exportación compatible de datos HP y recuperación de cálculos.
9. Cancelación/progreso de cálculos largos, tratamiento de señales muy grandes, revisión visual.
10. EXE completo: dependencias/avisos, ensayo desde carpeta aislada sin entorno Python ni fuentes, y auditoría contra los 109 menús más las rutas dinámicas de HP.

Usar docs/INVENTARIO_HP.md y el código HP como fuentes de alcance. Actualizar la matriz sólo con evidencia de implementación y pruebas, sin convertir filas incompletas en completas.

## Continuación: empaquetado y correlaciones

- Se identificó una dependencia ICU incompatible: Analysis-00.toc seleccionaba icuuc.dll de Poppler en el entorno externo. Esa DLL no exporta 20 funciones requeridas por Qt6Core. build_portable.ps1 ahora restringe PATH al entorno local y Windows, restaurándolo al finalizar.
- Se agregó operations.circular_convolution (N=max longitudes, relleno con ceros, eje desde cero, convención HP).
- Se agregó operations.correlation: auto/cruzada, lineal/circular, normalización energética estable y promedio periódico. Circular exige igual longitud y conserva los orígenes módulo N. La UI permite elegir modelo y escala; también accesible desde Fourier.
- No se ejecutaron pruebas nuevas en esta continuación. Las 33 pruebas mencionadas arriba corresponden al estado anterior, no validan estos cambios ni RC por frecuencia, escala logarítmica o el nuevo EXE.
- RC por frecuencia y componente conocido ya tiene implementación; falta validarla. Continúan pendientes los modelos continuos de correlación y la auditoría del resto de la matriz.

### Artefacto generado en esta continuación

- outputs/SignalLab-PC-dev.exe: compilación completada, 111045554 bytes.
- SHA-256: 624322729DE2DFC8F2E43311EFB572808C63C725B38B2D228EE0B419864793A0
- Incluye las incorporaciones de este lote; arranque y resultados aún sin validar en esta continuación.


## Compilación 0.2 generada

- EXE: outputs/SignalLab-PC-dev.exe (111120924 bytes).
- SHA-256: D26681E3AFC434C0199B643ABEA4CA8AD24D5AAF57C9C225D2C7E39D39053B42
- Compilación completada. No se ejecutaron pruebas nuevas ni se lanzó este EXE en esta continuación.
- outputs/manifest-dev.json registra la huella de cada módulo Python.
- La primera versión permanece en releases/v0.1.0; migración completa aún pendiente.

