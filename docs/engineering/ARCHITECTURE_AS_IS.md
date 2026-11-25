# Arquitectura actual de SignalLab PC

**Fase 00 · 24 de noviembre de 2026.** Línea base `16ffcbaee8356e41de6ed1e5e3410b607afe480f`. El rediseño local se inventarió aparte. Los límites que siguen describen las dependencias reales del código.

## Inventario y punto de entrada

| Alcance | Commit de referencia | Árbol local |
| --- | ---: | ---: |
| Python de aplicación, incluido `main.py` | 367 archivos, 46.580 líneas físicas | 375 archivos, 48.800 líneas físicas |
| Archivos `tests/test_*.py` | 58, 8.965 líneas | 58, 9.111 líneas |
| Dependencias internas, pares de módulos | 1.925 | 1.990 |
| Dependencias al nivel superior del módulo | 864 | 921 |
| Módulos que importan directamente Qt o su backend de Matplotlib | 173 | 178 |

Los conteos excluyen dependencias instaladas, documentación, historial y archivos generados. El catálogo local declara **30 herramientas y 84 rutas**. Una ruta puede representar una variante dentro de una herramienta. `main.py` y el entry point `signallab-pc` llevan a `signallab_pc.__main__`. Ese despachador atiende la interfaz, los procesos simbólicos y la autoverificación empaquetada.

| Área | Capacidades y módulos existentes |
| --- | --- |
| Señales | Fórmulas, tramos, muestras, CSV, JSON y MATLAB, ventanas, edición, medidas, aritmética, convolución y correlación. `engine`, `model`, `operations`, `continuous`, `matlab_import`. |
| Sistemas y filtros | Transferencias, respuesta temporal y frecuencial, diagramas, estados MIMO, diseño FIR/IIR e ideal, raíces, ganancia, fase y conversiones. `filters`, `realization_graph`, `temporal_analysis`, `state_space`, `course_tools`, `frequency_filter`. |
| Fourier y muestreo | DFT/FFT, DTFT, CTFT, series, espectros y densidades, Hilbert, STFT, aliasing, reconstrucción y cambio racional de tasa. `fourier`, `fourier_ordinary_pairs`, `dsp_extensions`, `sampling`. |
| Laplace, Z y CAS | EDO, recurrencias, transformadas directas e inversas, ROC, condiciones y cálculo simbólico. `symbolic`, `laplace_algebra`, `z_algebra`, `z_inverse`, `cas_engine`. |
| Señales aleatorias y precisión | Realizaciones reproducibles, estimación AR, procesos ARMA, estimadores de correlación, cuantización y ejecución de filtros. `random_signals`, `random_models`, `ar_estimation`, `precision`, `filter_arithmetic`. |
| Escritorio y distribución | Biblioteca de resultados, sesiones, informes, gráficos, cálculo cancelable, importación y actualización. `workbench`, `toolbox`, `plot_view`, `results_browser`, `project`, `session_desktop`, `update_ui`. |

## Dependencias observadas

```mermaid
flowchart TD
    Entry[__main__] --> Qt[WorkbenchWindow / ToolPage / paneles Qt]
    Entry --> Worker[Proceso simbólico JSON]
    Qt --> Work[QThreadPool / jobs]
    Qt --> Presentation[Informes, figuras y selección de resultados]
    Qt --> Sessions[session_desktop / session_fields]
    Work --> Engines[Motores numéricos y simbólicos]
    Worker --> Engines
    Engines --> Models[Signal / Transfer / StateModel]
    Engines --> Libraries[NumPy / SciPy / SymPy]
    Qt --> Project[Project / registro de procedencia]
    Sessions --> Project
    Project --> Models
    Project --> Atomic[JSON y escritura atómica]
    Presentation --> Qt
```

El diagrama agrupa módulos. La última flecha refleja dependencias de presentación que vuelven a la interfaz, por ejemplo `workflow_inputs → toolbox` mediante una importación local. El registro completo se generó con el AST de los dos árboles. Se contó un par por módulo origen y destino, sin inferir importaciones dinámicas o la ejecución efectiva de una rama.

- **Comprobado.** En ninguno de los dos árboles se observó un componente fuertemente conexo de dos o más módulos con sólo las importaciones al nivel superior. Al incluir las importaciones locales aparecen cinco componentes. El mayor abarca 224 módulos en el commit y 229 en el árbol local. El resultado identifica acoplamiento estructural, aunque las cargas diferidas evitan que todas esas referencias se activen al iniciar.
- **Comprobado.** Los cuatro componentes pequeños son `custom_appearance ↔ theme_presets`, `library_catalog ↔ library_titles`, `probe_data ↔ signal_plot` y `update_channels ↔ update_download`. Revisar esos límites es más manejable que dividir primero el componente mayor.
- **Comprobado.** `toolbox` es el mayor concentrador. En el árbol local referencia 98 módulos y tiene 37 importadores. Los más reutilizados son `resources` (99), `jobs` (69), `result_summary` (67), `model` (55) y `numeric_input` (55).
- **Inferencia.** La separación más útil es extraer contratos de datos y de ejecución de los flujos que hoy atraviesan `ToolPage`, `PanelContext` y el registro de resultados. Cambiar archivos de carpeta antes de definir esos contratos trasladaría las dependencias existentes.

## Modelos y persistencia

| Representación | Contrato actual | Condición que debe preservar una migración |
| --- | --- | --- |
| `model.Signal` | Vector finito en `complex128`, eje uniforme. Índice discreto `int64` con paso 1. Origen y paso flotantes en dominios continuo y frecuencial. Metadatos de reloj y definición. | Mantener índices grandes exactos, invalidación de fórmulas al editar, unidades y procedencia. Una captura I/Q con huecos o más de un canal necesita un contrato adicional. |
| `filters.Transfer` | Coeficientes y dominio s/z, representación SOS cuando corresponde, avances y período opcional. La ROC se registra aparte de la expresión racional. | Mantener distinción entre estabilidad BIBO, interna y ROC. Conservar retardos y avances al intercambiar fórmulas y coeficientes. |
| `state_space.StateModel` | Matrices complejas A/B/C/D con dimensiones MIMO validadas. `dt=None` representa continuo. | Mantener orientación de canales, modos ocultos, rango numérico y semántica de retención. |
| `symbolic` / `symbolic_process` | Solicitudes y resultados JSON con expresión, condiciones, notas y salida numérica opcional. `jobs` ofrece cancelación cooperativa. | Versionar el contrato antes de convertirlo en API pública. Mantener resultados no evaluados, sólidos y distribucionales como estados diferenciados. |
| `project` / `session` | Proyectos compatibles con esquemas 1 y 2. Sesiones compatibles con 1, 2 y 3. Identidad, dependencias y acciones de restauración separadas. | Conservar importación de ambos formatos, escritura atómica, rechazo antes de reemplazar la sesión y exportación del cierre transitivo de un resultado. |

`SessionController` y `session_fields` son adaptadores Qt. El formato persistente tiene un motor propio, pero las entradas recuperables dependen de nombres de controles y sinónimos de rutas. Este es un punto de compatibilidad para cualquier reorganización de vistas. Las importaciones MATLAB utilizan un analizador acotado para `.m`, SciPy para MAT tradicionales e h5py para MAT 7.3. La biblioteca educativa usa recursos JSON validados y distribuidos con la aplicación.

## Criterios de verificación

El grafo se deriva recorriendo `ast.Import` y `ast.ImportFrom` para `main.py` y `signallab_pc/**/*.py`. Resolver los niveles relativos antes de contar los pares. Separar los nodos de importación presentes directamente en `Module.body` de las demás apariciones. Calcular componentes fuertemente conexos sobre ambas versiones del grafo. El código cargado por nombre, el metacódigo y los PyInstaller hooks se revisan aparte. Un módulo sin importadores estáticos puede ser un punto de entrada o un recurso dinámico.

La arquitectura objetivo y su orden de adopción se documentan en [ROADMAP](ROADMAP.md). Los hallazgos de complejidad y duplicación están en [TECHNICAL_DEBT](TECHNICAL_DEBT.md).
