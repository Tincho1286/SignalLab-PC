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
- [Compilación verificable y firma](signing.md).
- [Almacenamiento de versiones](storage.md).
- [Contribuciones](../../CONTRIBUTING.md).

La interfaz, el modelo de datos y los motores compartidos evolucionan conservando las convenciones de señales, sistemas y resultados. Las variantes nuevas se integran en el catálogo existente antes de crear herramientas duplicadas.
