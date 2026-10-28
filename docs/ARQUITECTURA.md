# Arquitectura propuesta y primera implementación

```text
UI de escritorio (PySide6)
  ├── Catálogo de navegación y estado explícito
  ├── Tabla editable, gráfico interactivo Matplotlib, formularios
  └── Operaciones fuera del hilo UI cuando el cálculo pueda ser largo
          ↓ comandos / resultados tipados
Motor matemático (NumPy + SciPy; SymPy sólo para expresiones exactas)
          ↓ Signal + metadatos
Representación de señales (muestras complejas, dominio, eje, unidades)
          ↕ adaptadores
Persistencia e intercambio (JSON nativo complejo, CSV tabular, más adelante formatos HP explícitos)
```

## Límites entre capas

- `model.Signal` es el único dueño de las muestras y del eje. Contiene números complejos sin limpieza visual, `domain`, `origin`, `step`, unidades, nombre, expresión y metadatos. La señal discreta impone índices enteros y paso 1.
- `engine.py` contiene cálculo sin dependencias de la UI. La evaluación de texto usa un AST restringido y funciones declaradas, no `eval`. Acepta conteos limitados por el presupuesto dinámico de memoria y el eje int64, no por los topes de la calculadora.
- `operations.py` porta medidas de registros finitos, transformaciones discretas del eje, suma, paridad, convolución/correlación lineales y DFT/IDFT, con ejes y convenciones explícitas. El banco de señales conserva resultados de esta sesión.
- `resources.py` estima memoria de trabajo con RAM física disponible y rechaza una operación antes de reservar buffers que excedan su presupuesto. No existe un máximo fijo de muestras propio de HP; siguen aplicando límites de int64, NumPy y la memoria real disponible.
- La tabla muestra como máximo 2.000 filas por página. El trazado reduce puntos a una envolvente de extremos cuando la señal es muy larga; estos dos límites afectan sólo a la vista, no a los datos, las operaciones ni los archivos exportados.
- `storage.py` codifica complejos como pares real/imaginario en JSON; CSV guarda ambas componentes y el eje por fila. No hay conexión automática al hardware HP ni importación implícita de las listas Home.
- `ui.py` compone la navegación, formulario, tabla paginada, gráfico y ciclo de intercambio. La generación por expresión y las operaciones sobre registros corren en `QThreadPool`; las opciones no implementadas se anuncian como pendientes y no crean datos ficticios.
- Los workers no tienen todavía cancelación ni barra de progreso; deben ampliarse para filtros y simulaciones posteriores.

## Representaciones y convenciones

Una lista finita no implica señal infinita o periódica. La DFT/IDFT migrada declara normalización, truncado/relleno con ceros y bins enteros; DTFT, frecuencia angular y Hz requieren implementaciones separadas con unidades explícitas. Las medidas calculadas describen sólo la ventana finita guardada. La representación de muestra no será la del impulso Dirac continuo; N/D se representará como valor no disponible y nunca se convertirá en cero. Tabla/exportación conservan originales; reducción gráfica es una vista derivada.

## Estructura actual

- `signallab_pc/model.py`: modelo tipado de señal.
- `signallab_pc/engine.py`: evaluador restringido y constructor de secuencias.
- `signallab_pc/storage.py`: intercambio JSON/CSV.
- `signallab_pc/catalog.py`: catálogo visible de navegación HP→PC.
- `signallab_pc/ui.py`: aplicación funcional de primera etapa.
- `docs/INVENTARIO_HP.md`: 109 llamadas literales a menús y sus opciones, extraídas del fuente completo; las opciones dinámicas se abren en sus funciones señaladas por `PUNTOS_ENTRADA_HP.txt`.

## Hitos siguientes

1. Ejecutar la suite de regresión y verificar la interfaz en Windows con señales de distinto tamaño.
2. Completar la paridad de señales, LTI, DTFT/series, transformadas simbólicas, muestreo, filtros y control.
3. Incorporar N/D y otros estados de muestra con semántica explícita, además de autocorrelación y modos periódicos.
4. Añadir cancelación, progreso y límites preventivos más precisos a los workers largos.
5. Auditar dependencias transitivas y licencias del instalador; construir y probar el `.exe` portable en Windows limpio.
