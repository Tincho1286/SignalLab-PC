# Objetivo vigente: laboratorio de Sistemas y Señales para PC

La UI por menús se conserva. El producto es un laboratorio conectado de señales, sistemas y cálculos numéricos y algebraicos, con el alcance funcional de HP como base y capacidades de PC ampliadas. No se limita a calculadoras aisladas ni requiere una señal global única. MATLAB/Octave expresan la capacidad buscada en esta especialidad, no una promesa de compatibilidad total de sus lenguajes o paquetes.

## Requisitos que siguen vigentes

1. Cubrir todas las funciones y menús HP inventariados; cerrar cada fila de MATRIZ_MIGRACION.md con evidencia específica. El inventario de 109 entradas es una referencia, no prueba de implementación.
2. Compartir señales, sistemas, expresiones y resultados entre herramientas, con procedencia, unidades y dominio. Mantener entradas propias por herramienta.
3. Permitir análisis numérico y algebraico del mismo sistema, conservando expresiones originales, condiciones y distinción entre exacto y aproximado.
4. Ampliar cálculo y visualización para PC: límites por recursos reales y precisión, cancelación, registros grandes, más opciones de análisis, comparación y exportación.
5. UI y documentación concebidas para PC. No trasladar literalmente textos o restricciones de la calculadora.
6. Vinculación bidireccional por capacidades y convenciones con la carpeta HP de referencia; sin modificar automáticamente la versión HP ni declarar equivalencia no auditada.
7. Distribución portable Python/Windows, conservando versiones publicadas y verificando el artefacto final.

## Incremento actual: proyecto compartido (fuente 0.6 en desarrollo)

Implementado: instantáneas de señales y transferencias, resultados simbólicos, procedencia por identificadores, selección desde cada entrada, reutilización de sistemas entre menús, incorporación no destructiva de proyectos y guardado atómico. Los cálculos numéricos básicos y Fourier publican sus resultados; los diseños de sistemas y cálculos simbólicos también. Los informes que no producen objetos todavía requieren revisión para integrarlos de forma homogénea.

Evidencia: tests/test_project.py (aislamiento, procedencia, persistencia, importación atómica, payload simbólico); work/project-preview/verification.json (recorrido UI generar → desplazar → DTFT, padres correctos y guardado). Estas verificaciones no prueban paridad completa ni todos los flujos.

Añadido: análisis algebraico y numérico de una misma definición, con coeficientes originales (incluidas fracciones), proyección numérica enlazada y respuesta causal opcional. Evidencia: tests/test_system_analysis.py y work/project-preview/system-verification.json. Todavía falta extender este modelo a todas las herramientas.

Pendiente: generalizar la representación original exacta y las vistas vinculadas; ampliar matrices/estado-espacio y demás opciones pertinentes; completar funciones HP pendientes, registro homogéneo de parámetros y cálculos, manejo de estados especiales, persistencia eficiente de grandes datos, editor/cursor/tabla y proyectos completos; auditoría de regresión y del EXE.

La referencia HP se cotejó por hash el 21/10/2026: 9EC7E69183AC50303A4EF0FDFAFD4B585F33D75D2164AE725E95574A75033DCB. El objetivo general permanece abierto.

## Incremento 0.10
Espacio de estados numérico MIMO, simulación, discretización y conversión de transferencias integrados al proyecto. Evidencia y límites en AVANCE_0_10.md. La representación matricial algebraica y la cobertura total permanecen pendientes.

## Vinculación por capacidades, esquema 1
Catálogo de las 57 rutas PC y 157 llamadas SSMenu HP con referencias de familia, convenciones y estados de auditoría separados. Comparador de capacidades, convenciones, menús y casos de referencia en ambos sentidos. Cinco casos compartibles aprobados en PC; HP no ejecutado. Coincidencia de hash con la carpeta HP canónica comprobada. Esto establece el mecanismo de revisión; aún falta auditar todas las subopciones y registrar propuestas concretas en ambas plataformas. Véase VINCULACION_CAPACIDADES.md.

## Incremento 0.12
Energía y potencia de expresiones por intervalo, en todo el eje y periódicas, con exacto/aproximado y muestras derivadas enlazadas. Evidencia y límites en AVANCE_0_12.md. Continúan pendientes la cobertura HP completa y las ampliaciones restantes.
