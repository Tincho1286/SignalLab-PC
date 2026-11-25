# Auditoría funcional de interfaz

El escritorio real de Windows permitió completar en una ventana de 640 × 420 lógicos la búsqueda rápida, selección de DFT, cálculo de la señal precargada, publicación de 64 valores y apertura de la figura independiente. En el gráfico se observaron magnitud discreta, fase, herramientas y cursores. Volver a Resultados mostró el registro publicado. El diálogo de salida abrió la operación de guardado y presentó los botones estándar de Qt en inglés. El resto de funciones se cubre con la suite integral y las capturas por panel.

La figura conserva la fase de coeficientes locales muy pequeños calculados por FFT. La vista y la tabla preservan esos valores. Se registra como mejora de interpretación indicar de forma diferenciada la fase sensible al redondeo, sin modificar los coeficientes científicos.

La interacción manual se realizó en la revisión del paquete 08. Las capturas Windows nativas se repitieron con la revisión final `459b9fc`. [Perfil y geometría](../validation/evidence/windows-display-459b9fc.json)
