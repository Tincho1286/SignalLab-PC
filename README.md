# SignalLab PC

Aplicación Python portable para Sistemas y Señales I y II. Desarrollo actual: **0.99.10**, en consolidación hacia 1.0. Señales Aleatorias conserva sus herramientas existentes como área visible junto a las demás; su ampliación queda para más adelante. Modulación y demodulación están excluidas por indicación del usuario.

## Usar la aplicación

Descargá el portable desde [SignalLab PC 0.99.10](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v0.99.10) con tu cuenta autorizada para el repositorio privado. La copia local actual está en outputs/SignalLab-PC-0.99.10-preview.exe. El portable incluye Python y sus dependencias. Las versiones anteriores se conservan; la primera está en `releases/v0.1.0`.

El escritorio usa azul noche, superficies de trabajo diferenciadas, bordes redondeados y acentos azules, menta y violeta. Los campos numéricos son monoespaciados y los informes conservan tipografía matemática. Fórmulas, ayudas ilustradas, figuras y documentos exportados comparten la paleta oscura.

Elegí un área y luego una herramienta de su lista directa, o abrila desde Inicio. Cada problema conserva sus entradas y resultados durante la sesión. Las opciones de dominio, operación o método se eligen dentro del problema. No hace falta crear una señal de proyecto antes de trabajar.

| Área | Herramientas que reúne |
|---|---|
| Señales | Crear y editar, transformar, sumar, multiplicar punto a punto, convolucionar, correlacionar y medir energía/potencia/RMS. |
| Sistemas LTI | Análisis de transferencia en frecuencia y tiempo, polos/ceros de consulta, realizaciones con integradores/retardos, interconexiones y estados. |
| Diseño de filtros | FIR/IIR, h[n] propia con ventana, filtros ideales/en frecuencia, diseño por ubicación de polos/ceros, modelos físicos, ganancia/fase y conversión. |
| Fourier y espectros | Fourier directa/inversa, DFT/DTFT, FFT/ventanas, series, densidades, Hilbert y STFT. |
| Muestreo y A/D | Muestrear, aliasing, reconstruir, cambiar tasa, cuantizar y relacionar frecuencias/período. |
| Laplace y Z | Transformadas directas/inversas y ecuaciones diferenciales. |
| Señales aleatorias | Generación de realizaciones, estadísticas, autocorrelación y autocovarianza. |

**Calculadora CAS** es un acceso general desde el lateral, la barra superior o Ctrl+Shift+C. Su hoja conserva entradas numeradas, resultados matemáticos, variables y funciones durante la sesión. Enter evalúa; Shift+Enter continúa la expresión; Ctrl+↑/↓ recupera comandos. F1 explica la sintaxis. El motor es SymPy y la forma de trabajo se inspira en xCAS, sin compatibilidad completa con Giac. Hoja permite consultar variables y exportar el trabajo; Resultado puede copiar o enviar expresiones a señales y sistemas.

Fórmula, Muestras, Archivo y Resultado son fuentes alternativas de entrada. Fórmula incluye edición por tramos. Las listas admiten constantes como `pi`, `1/3`, `10^(-3)` y complejos. La importación permite MATLAB, CSV y JSON. Exportar o enviar un resultado a otra herramienta es opcional; enviar copia los datos y requiere calcular en el destino. Cada variante conserva su borrador al volver; Copiar entrada permite reemplazarlo explícitamente. En Laplace/Z, Analizar X como H copia la expresión racional directamente al análisis de sistemas: el último resultado en Directa, o la entrada actual en Inversa.

Editar muestras permite trabajar con una secuencia discreta o un registro continuo muestreado. Abrir en tabla carga la entrada; Aplicar edición valida muestras, nombre y eje juntos. Resultado permite consultar el gráfico/valores, exportar o enviar a otra herramienta sin pasar por Resultados de la sesión. Una nueva edición no altera una salida ya aplicada o enviada.

Analizar un sistema reúne módulo lineal/dB, fase, retardo y polos/ceros. El eje puede ser lineal o logarítmico, con frecuencias siempre angulares. Los márgenes opcionales interpretan H como lazo abierto con realimentación negativa unitaria; son estimaciones de cruces en el intervalo evaluado y no un certificado de estabilidad. La respuesta completa se exporta a CSV/JSON. Cargar sistema permite abrir una transferencia JSON o usar un resultado anterior; conserva SOS y avances temporales. Conectar sistemas admite fórmulas por bloque y conserva los retardos/avances en cascada, paralelo y realimentación.

La pestaña Realización del análisis muestra las ecuaciones y un diagrama vectorial aparte. Permite zoom, desplazamiento y exportación SVG/PNG. Sus matrices se pueden enviar a Espacio de estados; las secciones SOS recibidas se conservan como cascada.

La biblioteca contiene explicaciones redactadas por herramienta: qué permite hacer, cómo preparar el cálculo, cómo interpretar la salida y sus condiciones. Las definiciones de los campos se consultan aparte y el glosario está enlazado desde la lectura. Los conceptos, funciones y CAS tienen páginas propias.

Ajustar ganancia y fase → Fase y compensación conserva la separación de fase mínima/paso todo y añade diseño FIR para aproximar una ganancia y un retardo de la cascada H·C en una banda. El informe mide el error en una rejilla independiente y permite comparar original, compensado y objetivo, exportar CSV y reutilizar el sistema seleccionado.

Cuantización y representación → Formatos y coeficientes reúne punto fijo Q y almacenamiento IEEE 754 binary16/32/64. Permite representar números o comparar coeficientes de H(z), con respuesta, radios de polos, tabla de conversiones y reutilización del filtro cuantizado. El estudio Filtrar con precisión finita añade la ejecución DF-II transpuesta, en polinomio o SOS conservadas: productos, sumas, salida y memorias cuantizados, acumulador Q ampliado, saturación o desborde cíclico, estados iniciales y detección de ciclos con entrada nula. Se exporta y reutiliza la salida; Hq representa sólo el almacenamiento de coeficientes.

Los gráficos se abren en figuras independientes. Los informes muestran fórmulas y condiciones; Valores permite consultar los datos completos. Editar entradas conserva el resultado anterior con aviso hasta recalcular. Las operaciones de Laplace/Z conservan sus entradas y resultados por separado.

- **Ctrl+K:** buscar en toda la app.
- **Ctrl+Enter:** calcular la opción activa.
- **F1:** ayuda de la herramienta.
- **F11:** concentrarse en el documento, ocultando o restaurando los paneles laterales.

## Unidades y alcance

Frecuencia discreta en rad/muestra; continua en rad/s. Fs es una tasa en muestras/s. Los índices discretos usan enteros y las muestras se dibujan con tallos. El tiempo continuo se representa en segundos. El retardo de grupo usa muestras en digital y segundos en analógico.

Los cálculos numéricos usan doble precisión. No se heredaron los límites pequeños de memoria de una calculadora: se comprueba el espacio de trabajo disponible. La tabla se pagina y las figuras pueden reducir la densidad visual de registros muy grandes sin cambiar los valores exportados.

Los cálculos simbólicos conservan condiciones y distinguen una expresión resuelta de una operación pendiente. Laplace directa es unilateral y su inversa causal; no se ofrece selección general de ROC bilateral. Z inversa algebraica utiliza descomposición polinómica de fracciones racionales y conserva raíces exactas definidas por sus polinomios cuando expandir radicales complica la fórmula. La ROC sigue distinguiendo secuencias diferentes. Un registro gráfico finito no reemplaza una secuencia infinita ni demuestra convergencia.

En FIR por especificaciones, las estimaciones de longitud y la comprobación de una rejilla no prueban un mínimo global ni cumplimiento entre todos los puntos. Los filtros ideales y los registros continuos numéricos tienen sus modelos y aproximaciones indicados en la ayuda. Los impulsos Dirac se conservan por posición/peso cuando la herramienta los admite y no se interpretan como alturas finitas.

Las realizaciones SOS se preservan en los recorridos documentados de cálculo y reutilización; editar coeficientes crea una definición polinómica. La importación `.m` admite el subconjunto numérico declarado en su diálogo: no ejecuta código MATLAB arbitrario.

## Estado y evidencia

- [Cierre vigente hacia 1.0](CIERRE_1.0.md): alcance, evidencia y trabajo abierto.
- [Cambios de 0.99.10: elección de Fourier y búsqueda por variante](DESARROLLO_0.99.10.md).
- [Cambios de 0.99.9: entrada continua y pesos Dirac](DESARROLLO_0.99.9.md).
- [Cambios de 0.99.8: resultados al CAS y Z inversa por propiedades](DESARROLLO_0.99.8.md).
- [Cambios de 0.99.7: conversión, cortes y plano s](DESARROLLO_0.99.7.md).
- [Cambios de 0.99.6: entradas coherentes entre variantes](DESARROLLO_0.99.6.md).
- [Cambios de 0.99.5: carga y reutilización coherentes](DESARROLLO_0.99.5.md).
- [Cambios de 0.99.4: Laplace bilateral y ROC](DESARROLLO_0.99.4.md).
- [Cambios de 0.99.3: transformaciones coherentes](DESARROLLO_0.99.3.md).
- [Cambios de 0.99.2: reloj físico de sistemas discretos](DESARROLLO_0.99.2.md).
- [Cambios de 0.99.1: escritorio oscuro y redondeado](DESARROLLO_0.99.1.md).
- [Cambios de 0.99: escala estable de gráficos](DESARROLLO_0.99.md).
- [Cambios de 0.98: suma y producto coherentes](DESARROLLO_0.98.md).
- [Cambios de 0.97: resultados de estados reutilizables](DESARROLLO_0.97.md).
- [Cambios de 0.96: longitud de ventana y simulación de estados](DESARROLLO_0.96.md).
- [Cambios de 0.95: multiplicación y enventanado de h[n]](DESARROLLO_0.95.md).
- [Cambios de 0.94: ubicación de filtros ideales](DESARROLLO_0.94.md).
- [Cambios de 0.93: DTFT inversa](DESARROLLO_0.93.md).
- [Cambios de 0.92: biblioteca común de resultados](DESARROLLO_0.92.md).
- [Cambios de 0.91: nitidez de las fórmulas](DESARROLLO_0.91.md).
- [Cambios y comprobaciones de 0.90](DESARROLLO_0.90.md).
- [Cambios y comprobaciones de 0.89](DESARROLLO_0.89.md).
- [Cambios y comprobaciones de 0.88](DESARROLLO_0.88.md).
- [Cobertura vigente y carencias de Sistemas I/II](COBERTURA_SYS_I_II_ACTUAL.md). Los programas originales y las notas históricas permanecen como referencia.

Las notas DESARROLLO de cada versión registran cambios y comprobaciones dirigidas. Su presencia no certifica todos los ejercicios ni todas las combinaciones de parámetros. El usuario confirmó el funcionamiento del portable y realiza la revisión general de uso. No se exige guardar y recuperar sesiones para esta etapa.

## Ejecutar o compilar el código

Python 3.12 de 64 bits en Windows. Desde la carpeta del proyecto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m signallab_pc
```

También está disponible `setup_windows.ps1`. Para generar el portable con el entorno preparado:

```powershell
.\build_portable.ps1 -Name SignalLab-PC-0.99.8-preview
```

El proyecto PC es independiente. Las referencias de la calculadora se conservan como material de consulta en `references`; la ubicación de origen está documentada en `references/REFERENCE.md`, sin sincronización automática. El historial del README anterior está en [docs/README_HISTORICO_2026-10-27.md](docs/README_HISTORICO_2026-10-27.md).

Diseñar por polos y ceros incluye Respuesta en frecuencia (módulo, fase y retardo de grupo) y envío a Análisis de sistemas desde Usar filtro en. Se permiten y conservan avances digitales, incluidos los diseños con más ceros que polos. El sistema exportado con avance usa versión 2 del formato de transferencia para que una aplicación anterior no pueda abrirlo ignorando ese factor.

Fase y compensación → Reconstruir módulo y fase trabaja con módulo lineal/dB o fase desenrollada propios. Construye una respuesta periódica bajo hipótesis de fase mínima, con desplazamiento explícito y referencia de ganancia desde fase. H puede reutilizarse en filtros definidos en frecuencia; el registro temporal aproximado no se presenta como un FIR exacto.


La biblioteca **Resultados** reúne las salidas calculadas: señales, sistemas, modelos de estados, expresiones y tablas/informes. El CAS guarda allí sus valores exactos, sin copiar todo el entorno de la hoja. El filtro Expresiones y Usar selección en permiten recuperar una fórmula en CAS, transformadas, señales, medidas o análisis de sistemas según su variable; las condiciones permanecen en el resultado original. Los destinos con variantes se ofrecen dentro del mismo problema.


**DTFT inversa:** Transformada de Fourier → Discreta → DTFT inversa → Numérico / Algebraico. La primera integra un período muestreado de X(ω), en rad/muestra; la segunda obtiene x[n] por propiedades de Z o integración simbólica. La salida admite índices negativos y se guarda en Resultados. Las fórmulas numéricas ajustan el paso para cubrir 2π; los espectros de archivo/resultado conservan su eje.


Filtro ideal o definido en frecuencia está en **Diseño de filtros → Ideales y conversión**. La ubicación se comparte con el buscador, las ayudas y los destinos de reutilización.


**Sumar o multiplicar señales:** reúne Suma y Producto en Señales, con dominio discreto/continuo y entradas independientes en dos pestañas. La suma cubre ambos registros; el producto conserva el intervalo de la primera señal. **Diseñar filtro → FIR → Digital → Definir por → h[n] propia:** aplica una ventana estándar de longitud L independiente o una w[n] propia. Se elige centrarla o fijar su primer índice. Una fórmula h[n] se evalúa sobre ese intervalo; un registro finito usa cero fuera de sus datos. Muestra módulo, fase, retardo de grupo y secuencias; guarda las salidas en Resultados. Retardar un registro con inicio negativo es opcional. No se normaliza automáticamente la ganancia.


**Espacio de estados:** Respuesta temporal usa una entrada independiente por canal, con fórmula/tramos, muestras, archivo o resultado. Conserva el primer índice o instante, evalúa las secuencias en n entero y verifica el reloj de las señales discretas frente a T. El estado inicial corresponde al comienzo del registro. La respuesta en frecuencia discreta usa rad/muestra; la continua usa rad/s.


**Resultados de estados:** Obtener transferencia muestra H(s)/H(z) primero en el informe, con acciones directas para analizar, reutilizar y exportar. Los otros estudios ofrecen Usar modelo calculado en, conservando matrices, dominio y T. Exportar modelo genera un JSON nativo que se abre desde Cargar modelo; si hay varios modelos se puede elegir cuál usar. Las acciones conservan el último resultado al editar los campos.


La suma continua interpola linealmente las partes ordinarias en el intervalo conjunto, sobre una rejilla uniforme basada en el menor paso de entrada y ajustada a sus extremos. Los impulsos Dirac se suman por posiciones/pesos sin representarlos como muestras finitas. Suma y Producto conservan borradores propios; Copiar entrada copia las dos fuentes y el dominio. La suma discreta mantiene el reloj registrado y rechaza relojes incompatibles.


**Escala de gráficos:** la vista automática evita ampliar artificialmente señales casi nulas o variaciones diminutas alrededor de un nivel constante. El control Detalle vertical de cada figura permite ajustar el eje a esas variaciones. Un aviso al pie indica cuándo interviene la escala estable. No se redondean ni se borran muestras: tabla, cursor y exportación numérica conservan los valores originales. El zoom manual, las escalas logarítmicas, los diagramas de raíces y los gráficos dedicados a errores conservan su comportamiento.


**Presentación 0.99.1:** Inicio destaca Crear señal, Analizar sistema y Diseñar filtro. Las áreas usan tarjetas con iconos y acentos propios; la navegación y los selectores tienen estados redondeados. Calcular permanece visible en la cabecera y las acciones de reutilización se distinguen en menta. Las fuentes, el catálogo y los cálculos se conservan.


**Reloj físico de H(z):** un sistema puede conservar su período T desde estados, una conversión o un archivo. Respuesta temporal lo muestra en un campo opcional; no cambia n ni las frecuencias en rad/muestra. Las entradas con Fs conocida deben ser compatibles. Las salidas conservan el reloj y los archivos de transferencia con T usan el formato nativo 3; se siguen leyendo los formatos 1 y 2. Dejar T vacío permite trabajar sólo por índices o tomar el reloj de la entrada.


**Transformar una señal:** Desplazar, Invertir, Amplitud y Par e impar tienen opciones directas tanto discretas como continuas. Transformación afín reúne A, a y t₀ cuando se necesitan juntos. El informe muestra primero la relación matemática; la señal original se dibuja al abrir su pestaña. Las salidas transformadas conservan la fórmula original como procedencia, no como si describiera sus nuevos valores. Par e impar continuo usa un registro interpolado simétrico y conserva los términos Dirac.

## Almacenamiento de desarrollo

La compilación portable limpia sus intermedios al terminar correctamente. Los ejecutables históricos idénticos pueden compartir espacio sin perder sus rutas ni versiones. Ver [mantenimiento y compilación](ALMACENAMIENTO.md).

## Código y versiones privadas

[Repositorio privado](https://github.com/Tincho1286/SignalLab-PC) · [Versiones descargables](https://github.com/Tincho1286/SignalLab-PC/releases). Los portables se guardan como adjuntos de releases, fuera del historial Git. Consultá [publicación y recuperación de históricos](RELEASES_GITHUB.md).
