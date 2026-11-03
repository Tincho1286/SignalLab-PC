# Fiabilidad de las transformadas

SignalLab conserva una definición matemática de la entrada junto con cada resultado de Z, Laplace y Fourier. Incluye la fórmula original, la expresión efectiva exacta, la variable, el dominio, el soporte o intervalo de integración, las condiciones de entrada y los valores completados por continuidad. La representación interna conserva los índices enteros y las constantes exactas.

## Valores por continuidad y dominio

En una secuencia, cada muestra contribuye a la suma. Por eso sin(pi*n)/(pi*n), completada con 1 en n=0, mantiene esa muestra al calcular Z o DTFT, incluso con desplazamientos o soportes truncados. Un valor finito asignado por tramos tiene prioridad sobre la extensión automática. Un polo real entre dos índices no se trata como una muestra indefinida; un polo sobre un índice del soporte se rechaza cuando puede identificarse exactamente.

En una integral ordinaria, cambiar el valor aislado de una función no cambia su transformada. La definición original permanece registrada, pero las ramas aisladas pueden retirarse de la expresión de integración para facilitar el reconocimiento de los pares. Los impulsos Dirac mantienen sus pesos y su tratamiento de distribuciones.

Z y DTFT comparten la preparación de la secuencia. La sustitución z=exp(i*w) utiliza los pares de Z sólo cuando sus condiciones permiten el círculo unitario completo. Los pares de Fourier que existen únicamente sobre ese círculo, como la sinc bilateral, conservan su tratamiento propio.

## Estado de un resultado

El informe distingue una expresión obtenida, una expresión con condiciones, un resultado parcial, un cálculo sin resolver y la ausencia de una región de convergencia. Una operación pendiente dentro de una fórmula no se convierte en una solución por tener activada una marca de resultado evaluado. Obtener una fórmula no equivale a demostrar independientemente su identidad.

La definición y las notas de continuidad se conservan en Resultados, la exportación del registro y la procedencia del resultado enviado al CAS. Las condiciones originales acompañan la expresión importada; no se convierten automáticamente en supuestos nuevos de la hoja CAS.

## Control antes de construir un portable

Los constructores oficiales de Windows y Linux ejecutan `tools/check_math.py` antes de empaquetar. Si falla, la construcción se detiene. El control contiene 21 pruebas con casos y variantes: impulsos y sinc, soporte y desplazamientos, valores explícitos por tramos, polos verdaderos, pares geométricos y logarítmicos, ROC, Laplace bilateral, Dirac, Fourier e inversas, conservación de metadatos y transporte al CAS.

Las referencias se expresan mediante fórmulas conocidas y valores de borde; las comprobaciones de ida y vuelta son complementarias. GitHub ejecuta el mismo control en Windows y Linux al cambiar el código matemático y en las propuestas de cambios. La procedencia de cada portable registra el resultado y las versiones de las dependencias.

Para ejecutarlo localmente:

```powershell
.\.venv\Scripts\python.exe -B -X utf8 tools/check_math.py
```

El informe local se guarda en `work/math-checks.json`. Este control cubre referencias concretas: no certifica todas las expresiones posibles ni reemplaza las condiciones de convergencia de cada cálculo. Las comparaciones numéricas aisladas tampoco constituyen una prueba de identidad general.
