# SignalLab PC

Escritorio de señales y sistemas para Windows, escrito en Python. Versión actual de desarrollo: **0.72**, orientada a Sistemas y Señales I y II. La primera versión se conserva en `releases/v0.1.0`.

La navegación ofrece seis áreas principales con una lista directa, sin árboles de submenús. Inicio permite abrir las herramientas directamente. Hay 31 problemas públicos y 72 variantes internas; las herramientas estadísticas existentes quedan como acceso secundario. Analizar un sistema reúne frecuencia, polos/ceros y respuesta temporal; Diseñar filtro reúne FIR e IIR. Las entradas distinguen Fórmula, Muestras, Archivo y Resultado, y aceptan constantes matemáticas en las listas. Cada herramienta conserva sus datos, con reutilización opcional. Ctrl+K busca en toda la aplicación y Ctrl+Enter calcula la opción activa.

Estado de la primera estable: [CIERRE_1.0.md](CIERRE_1.0.md). Cambios y comprobaciones: [DESARROLLO_0.72.md](DESARROLLO_0.71.md). Los documentos de versiones anteriores se conservan como referencia histórica.

## Ejecutar en Windows

Requiere Python 3.12 de 64 bits. En PowerShell, desde esta carpeta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m signallab_pc
```

También se puede iniciar con `.\setup_windows.ps1` para crear el entorno e instalar las versiones fijadas.

El flujo permite escribir una expresión o secuencia compleja, editar muestras o el índice inicial, usar desplazamiento, inversión, escala, suma y partes par/impar, consultar medidas de la ventana finita, convolucionar y correlacionar secuencias, calcular DFT/IDFT, exportar CSV/JSON y reimportar. Las secuencias discretas conservan índices enteros y paso 1; eje, origen, unidades y metadatos viajan con la señal.

No se conserva el límite fijo de muestras de la calculadora. Los tamaños se admiten hasta el límite del eje entero y del espacio de direcciones, con una estimación previa de RAM disponible para cada cálculo. La tabla se pagina y la vista gráfica se reduce por densidad en señales muy grandes; ambas decisiones son sólo de presentación.

## Vínculo de referencia HP

El origen HP Prime 5.0 es `C:/Users/lesca/Documents/Software_Apps/SignalLab Hp Prime/SignalLab_5.0/SignalLab_App_5.0.hppl` (sólo lectura). El proyecto conserva una copia congelada en `references/SignalLab_App_5.0.hppl`; ambas tienen el hash indicado en `references/REFERENCE.md`. La carpeta PC vive como hermana en `C:/Users/lesca/Documents/Software_Apps/SignalLab PC`. No existe sincronización automática con HP Prime.

## Estado

- Arquitectura y trazabilidad: `docs/ARQUITECTURA.md`, `docs/MATRIZ_MIGRACION.md`.
- Dependencias, documentación consultada y notas de distribución: `docs/DEPENDENCIAS.md`.
- Casos de regresión compartibles: `tests/casos_regresion.json`.
- La distribución prevista es un solo `.exe` portable con Python, la interfaz y sus dependencias incluidas. Existe una compilación de desarrollo; la validación del ejecutable actualizado y la paridad completa siguen pendientes; los archivos de intercambio se guardan por separado.

## Ejecutable portable

Con el entorno de desarrollo preparado, ejecutá `build_portable.ps1` para generar un solo ejecutable mediante PyInstaller en modo `onefile`, en `outputs/SignalLab-PC-0.72-preview.exe`. La compilación debe correrse y verificarse en Windows con Python 3.12; al destinatario no se le pedirá instalar Python. El arranque de un archivo puede demorar algo más mientras prepara su contenido.

## Ampliación en curso

Se incorporaron filtros FIR/biquad/RC, bilineal, respuesta y polos/ceros al panel Filtros / LTI. También se incorporaron autocorrelación, correlación circular, normalización energética y promedio periódico, y convolución circular con la convención de relleno HP. Estas últimas incorporaciones aún no tienen validación ejecutada. No se heredan los topes de 1024/4096 muestras de HP; se conserva la comprobación de recursos disponibles.

## Primera versión y desarrollo actual

La primera versión no se sobrescribe. `releases/v0.1.0/manifest.json` registra las huellas del EXE y del código guardado. Los próximos cambios se compilan en `outputs/SignalLab-PC-dev.exe`. Las incorporaciones de 0.2 están pendientes de pruebas y de validación del ejecutable; ver `docs/VERSION_0_2.md`.

## Corrección visual 0.2.1

La salida actual es `outputs/SignalLab-PC-0.2.1-dev.exe`. Corrige los formularios comprimidos con alturas mínimas, filas separadas y desplazamiento. Se revisaron capturas de los paneles a 1366 × 698 y de Crear/editar a 1080 × 650; ver `docs/UI_0_2_1.md`. Los EXE anteriores se conservan.
