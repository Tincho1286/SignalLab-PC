# Validación de estimaciones de memoria

La medición conserva el pico residente antes y después, además de la capacidad disponible y la estimación de la operación. El pico del proceso comprende Python, NumPy, bibliotecas y entradas preparadas. Los presupuestos de cálculo expresan admisión de arreglos y etapas, por lo que la comparación los distingue del RSS total.

Los proyectos JSON copian estructuras Python y materializan listas de valores. El banco admite estos casos con un cribado conservador de 1024 bytes por muestra de entrada y deja los tamaños superiores a 262 144 para mediciones dedicadas. Esta cifra es un control del ensayo.
