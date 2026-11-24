# Desarrollo

[← Documentación](../README.md)

## Preparar el entorno

El proyecto usa Python 3.12 de 64 bits. Desde la raíz, en PowerShell:

```powershell
.\setup_windows.ps1 -NoLaunch
.\.venv\Scripts\python.exe -B main.py
```

El primer comando prepara el entorno y las dependencias fijadas; el segundo abre la aplicación. También se puede crear un entorno Python 3.12 e instalar `requirements-lock.txt` manualmente.

## Control matemático

Antes de empaquetar, los constructores oficiales ejecutan `tools/check_math.py`. La [guía de fiabilidad](../mathematical-reliability.md) describe las referencias y el alcance. Un fallo bloquea la construcción; `work/math-checks.json` conserva el informe local.

## Estructura

```text
signallab_pc/    Aplicación, motores, modelos y recursos
tests/          Casos existentes de cálculo y comportamiento
tools/          Herramientas de mantenimiento y publicación
docs/           Guías, alcance, versiones y archivo histórico
references/     Referencias técnicas de la implementación original
.github/        Plantillas para errores y propuestas
```

Los directorios `.venv/`, `work/`, `build/`, `dist/`, `outputs/` y los ejecutables son locales y quedan fuera de Git.

## Guías técnicas

- [Arquitectura](architecture.md).
- [Dependencias](dependencies.md).
- [Compilar y publicar](releases.md).
- [Verificación y firma de las distribuciones](signing.md).
- [Almacenamiento de versiones](storage.md).
- [Contribuciones](../../CONTRIBUTING.md).

La interfaz, el modelo de datos y los motores compartidos evolucionan conservando las convenciones de señales, sistemas y resultados. Las variantes nuevas se integran en el catálogo existente antes de crear herramientas duplicadas.

La [auditoría incremental de noviembre de 2026](audit-2026-11.md) documenta las correcciones, el mapa de módulos, los ejemplos educativos y la comprobación integral con `python tools/check_integral.py`.

## Cambios de documentación

Las correcciones editoriales revisan enlaces, versiones y coherencia entre guías y Releases. No requieren recompilar una distribución si no cambian su código ni sus recursos. Las notas publicadas deben conservar los límites históricos y no atribuir funciones nuevas a un ejecutable anterior.

## Herramientas interactivas en desarrollo

La 1.8.1 incorpora comparación FIR por ventanas, selección visual de ROC, inspectores de recurrencias y convolución y medidas espectrales de ventanas. La [guía de análisis interactivo](../interactive-analysis.md) explica sus controles y límites; estas funciones se distribuyen en los paquetes propios de la 1.8.1.

## Sesiones de escritorio

Los archivos `signallab-project` de esquema 1 o 2 siguen siendo archivos de
resultados. Se pueden incorporar a la biblioteca actual o abrir en una sesión
vacía. La incorporación reasigna identificadores para evitar colisiones.

Una sesión completa usa `signallab-session`. El esquema 2 conserva también la
procedencia y las condiciones activas de las expresiones reutilizadas, junto
con las matrices y las entradas por canal de la simulación de estados. Al abrir
un archivo del esquema 1 se conservan los datos disponibles; las condiciones
que el archivo nunca guardó quedan sin definir. Un lector del esquema 1 puede
recibir un archivo de resultados `signallab-project` por separado.

La sesión incluye el documento
de proyecto, las herramientas visitadas, los documentos abiertos, las entradas
editables compatibles y los identificadores de los objetos utilizados. Conserva
los identificadores de la sesión y valida referencias y esquemas antes de
reemplazar el trabajo activo. Las entradas todavía sin calcular se guardan como
texto y se interpretan recién cuando el usuario calcula. Un lector que solo
entiende proyectos necesitará una exportación de resultados por separado.

La recuperación automática es local. Revisa los cambios cada 30 segundos y
guarda cuando la sesión cambió y no hay un cálculo en curso. Solo reemplaza el archivo
anterior tras escribir y sincronizar el nuevo archivo por completo. Al inicio,
SignalLab ofrece recuperarlo y comunica qué se restauró. Cerrar normalmente
después de guardar o descartar elimina ese punto. La recuperación no incluye
cálculos en curso, ventanas de gráficos, historial del CAS ni preferencias de
la aplicación. Los resultados previos se consultan en la biblioteca. El esquema
admite los formularios, señales de entrada, transferencias cargadas, tablas de
muestras y diagramas aplicados. Los selectores asociados a resultados se
habilitan cuando volvés a calcular. El historial de deshacer y los cambios de
un editor de diagramas que sigue abierto sin aplicar quedan fuera del esquema.

## Distribución y cálculos reproducibles

Python 3.12 y `requirements-lock.txt` definen el entorno de prueba. Al validar
una distribución, compará la lista de recursos del wheel o el portable con
`signallab_pc/assets`, incluidos los artículos anidados en `assets/library`.
Los constructores PyInstaller de Windows y Linux incluyen el directorio de
recursos de forma recursiva.

El actualizador comprueba la firma del manifiesto con la clave pública
distribuida. El hash SHA-256 comprueba que el archivo recibido coincide con
el descrito en ese manifiesto. Authenticode es una firma distinta que Windows
valida sobre el ejecutable o instalador mediante un certificado de firma de
código. Su comprobación depende del binario real. Los portables nativos y la
instalación de cada plataforma se verifican sobre sus propios artefactos.

Una exportación de resultados incluye el objeto y sus dependencias. Algunas
operaciones también conservan solicitudes y condiciones. Para ofrecer una
reproducción verificable hace falta un contrato adicional por herramienta con
todas las entradas, condiciones, unidades, método y versiones de ejecución.
La exportación existente conserva los datos disponibles y no genera scripts
que aparenten reconstruir parámetros faltantes.

En Resultados, **Resultado con dependencias** guarda la selección y toda su
procedencia registrada, también cuando elegís una señal o una transferencia.
El JSON individual de estos objetos sigue disponible para importarlos
directamente en una herramienta.
