# Verificación de escritorio en la continuidad 02C

## Windows real

Fecha 25/11/2026. Escritorio Windows interactivo, un monitor de 1366 × 768 a 96 DPI (100 %). Candidato `faef335bb7892cda92edc50a7c4f417a89b0415c`, ejecutado desde código fuente con Qt para Windows y datos sintéticos. El cliente se probó maximizado y a 640 × 420 lógicos (642 × 452 con marco en la captura).

- Mediante Ctrl+K se abrió Densidad de potencia con la expresión inicial `cos(pi*n/4)`, N = 64 y Fs = 100 Hz. El cálculo produjo un PSD bilateral con picos en ±12,5 Hz y abrió la figura independiente.
- En modo compacto Calcular, Ayuda, Abrir gráfico e Informe quedaron accesibles. La disposición compacta conserva Datos de entrada y Resultado por separado y permite desplazar el contenido verticalmente.
- Archivo → Sesiones → Guardar sesión completa ofreció los dos formatos. Se guardó y volvió a abrir el `.slproj` de prueba. SignalLab informó dos objetos recuperados y una herramienta restaurada. La pestaña de PSD y la entrada se conservaron. El gráfico se abre de nuevo con un cálculo y la biblioteca retiene el resultado guardado.

## Comprobaciones que requieren otro entorno de escritorio

En una sesión Linux real y en Windows con otros escalados, registrá SHA, sistema, gestor/compositor si corresponde, tamaño físico del monitor, escala del sistema y tamaño lógico de la ventana. Probá 100 % y 200 %. Agregá 125 % y 150 % donde estén disponibles. Si hay dos monitores con distinta escala, arrastrá la ventana y la figura entre ellos.

1. Abrí Densidad de potencia con Ctrl+K. Usá N = 64 y Fs = 100 Hz. Calculá Welch con segmento y solapamiento en automático. Confirmá los picos en ±12,5 Hz y el acceso a Calcular, Ayuda, Informe y Abrir gráfico con la ventana reducida.
2. Ingresá segmento 65. Debe señalarse el campo y conservarse el espectro previo. Borrá el segmento y recalculá. Cambiá a la figura y cerrala para verificar el retorno al informe.
3. Guardá el proyecto como `.slproj` y abrilo de nuevo. Confirmá los dos objetos, la pestaña y su entrada. Registrá resultado por paso y adjuntá una captura de cualquier corte, bloqueo o desplazamiento incorrecto.

La captura Xvfb y los factores de escala automatizados son evidencia complementaria. La comprobación Linux real y la transición entre monitores con diferente DPI siguen pendientes.

## Recuperación CAS en escritorio real

En el escritorio Windows de 1366 × 768, con ventana de 800 × 600 a 96 DPI, se evaluó `a := 2+3*i` y se dejó `a+` como borrador. El escritor produjo un checkpoint válido con la variable, el resultado publicado y el borrador. La recuperación desde la misma ventana llegó a un error al construir el nuevo panel cuando Qt enfocaba el anterior. Varios paneles usan `window` como atributo de Python y la detección de foco invocaba ese atributo como método.

Se consulta ahora el método de QWidget y se prepara la nueva hoja fuera del árbol activo antes de reemplazar la sesión. La regresión offscreen fija el foco en el propio panel anterior. La repetición en Qt para Windows real conservó `a+` y `2 + 3*i` en la ventana de 800 × 600. El diagnóstico del portable comprueba también la reapertura de la hoja CAS en SLPROJ.

Para completar las actas pendientes, repetí también el flujo CAS en los perfiles físicos del protocolo. Evaluá `a := 2+3*i`, dejá `a+` sin ejecutar y guardá una sesión `.slproj`. Abrila con la hoja aún enfocada y comprobá el valor complejo y el borrador. Verificá que el control de cálculo queda disponible y que un gráfico existente puede moverse al otro monitor sin perder sus controles. Registrá los pasos según el entorno, el SHA y la escala aplicada por el sistema.
