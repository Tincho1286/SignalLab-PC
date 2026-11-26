# Verificación de escritorio en la continuidad 02C

El estado vigente de Linux está en [Aprobación de Linux de escritorio](#aprobación-de-linux-de-escritorio).

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

## Medidas de frecuencia en el candidato 623c9dd

El 25/11/2026 se ejecutó `623c9ddcc2460485b549e864fa86ddc6b7cba407` desde el código fuente con Qt `windows`, en un perfil descartable. El monitor físico de 1366 × 768 registró 96 DPI y DPR 1.0. La misma herramienta se usó a 800 × 600 lógicos y maximizada.

- En Análisis LTI se calculó `H(s)=1/(s+1)`. El cruce de media potencia fue 1 rad/s con módulo 0.7071067812. Al ingresar `pi/0` como límite final, Cruces señaló el campo y conservó su tabla.
- Comprobar bandas volvió a calcular con el borrador de Cruces intacto. En 0 a 10 rad/s devolvió mínimo 0.09950371902 en 10 y máximo 1 en 0. Los dos estudios quedaron guardados en una sesión sintética y el lector recuperó sus valores.
- Abrir gráfico quedó desactivado al pasar de la disposición compacta a la amplia. La pestaña Frecuencia todavía abrió su ventana independiente. Restaurar el tamaño inicial reactivó la acción de cabecera. La causa es el registro de un contenedor de la disposición como si fuese una pestaña de figura. El cambio posterior al candidato se valida por separado.

En `87b74ed`, volver a calcular `H(s)=1/(s+1)` en modo compacto y maximizar conservó habilitada la acción de cabecera. Abrir gráfico mostró la figura de frecuencia y cerrarla devolvió el foco al informe. Se usó el mismo monitor a 96 DPI. [Corrección y regresión](../IMPLEMENTATION_LOG.md#25-de-noviembre-de-2026--c-08--figuras-al-cambiar-de-ancho-de-ventana)

El entorno no dispone de un escritorio Linux ni de un segundo monitor con otro DPI. Las pruebas con Linux real y escalados físicos adicionales siguen pendientes.

## Acta Windows del candidato a80508c

El 26/11/2026 se ejecutó `a80508c224d902ce225c6b6cc66fd090210c52b2` desde su árbol limpio con Qt `windows`, sin factores de escala de prueba y con un perfil descartable. Se usó un monitor físico de 1366 × 768.

| Escala nativa | Tamaño lógico | Flujo | Resultado observado |
| --- | --- | --- | --- |
| 125 % · 120 DPI Win32 · DPR 1,25 | Ventana de 720 × 450, luego maximizada en pantalla lógica de 1093 × 614 | Análisis LTI, calcular con los coeficientes iniciales, maximizar, abrir Frecuencia desde la cabecera y cerrar la figura | El informe conservó el resultado y la acción Abrir gráfico. Se vieron módulo, fase y retardo con eje en rad/s. Al cerrar la figura volvió el informe y la acción siguió habilitada. |
| 100 % · 96 DPI Win32 · DPR 1,0 | Ventana de 800 × 600 | CAS, evaluar `a := 2+3*i`, guardar `a+` como borrador en SLPROJ, cambiarlo a `b+` y reabrir el proyecto | Se recuperó `a+`. La siguiente evaluación `a+1` dio exactamente `3 + 3i`. |

Se leyó `GetDpiForWindow` y el DPR de Qt al arrancar cada instancia. El selector estándar de este equipo ofreció 100 % y 125 %. Se restauró el 100 % original al terminar la prueba de 125 %. Los perfiles automatizados de Linux siguen documentados aparte.

## Aceptación de los escalados de Windows

El 26/11/2026 el mantenedor informó que probó personalmente Windows al 150 % y 200 % y aprobó ambos perfiles. Esta declaración complementa las comprobaciones detalladas de 100 % y 125 % del acta anterior. El alcance aprobado para Windows comprende los cuatro escalados. La transición entre monitores de distinto DPI queda fuera de esta comprobación de escalados. [Registro de aprobación](../validation/EXCEPTION_APPROVAL_REGISTER.md#aprobaciones-del-mantenedor-del-26-de-noviembre-de-2026)

## Validación pendiente en Linux real

Para completar E-05, usá este mismo SHA en Linux con escritorio a 100 % y en los escalados nativos más altos que ofrezca el entorno. Repetí el cambio compacto a maximizado de Análisis LTI con `H(s)=1/(s+1)` y la reapertura de CAS de la tabla. Registrá los tamaños físicos y lógicos, si los controles se pueden alcanzar y el valor posterior a reabrir CAS. Para probar 720 × 450 lógicos al 200 %, el área utilizable del monitor debe ser de al menos 1440 × 900 píxeles físicos.

## Aprobación de Linux de escritorio

El 26/11/2026 el mantenedor informó que realizó las pruebas manualmente en otro escritorio Linux y aprobó E-05 en esa plataforma. El expediente acredita la aprobación mediante su declaración. La distribución, la sesión gráfica, la resolución, el escalado y el SHA ejecutado quedan sin consignar en esa declaración.

La repetición independiente requiere acceso a una sesión de escritorio Linux. Para esa repetición se conserva el protocolo anterior. [Decisión de aceptación](../validation/EXCEPTION_APPROVAL_REGISTER.md#resolución-de-e-05)
