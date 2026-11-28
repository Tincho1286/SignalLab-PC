# Protocolo de rendimiento

`tools/measure_rf.py` ejecuta dos tamaños por perfil en procesos separados con un hilo numérico. Cada prueba verifica al menos una relación física o matemática antes de registrar el tiempo. Se registra RSS máximo del proceso, mayor reserva observada en el perfil y parámetros. Las reservas son estimaciones de admisión. RSS incluye el intérprete y las bibliotecas que importa el perfil.

| Perfil | Tamaño base / doble |
| --- | --- |
| Conversión y medidas de red | 2 048 / 4 096 frecuencias de cuatro puertos |
| Cascada de dos líneas | 8 192 / 16 384 frecuencias |
| Intercambio Touchstone | 4 096 / 8 192 frecuencias de dos puertos |
| Bessel de orden ocho | 8 192 / 16 384 frecuencias para el retardo |
| Espectros | Registros de 8 192 / 16 384 muestras, Zoom FFT y contorno radial |
| Incertidumbre | 16 / 32 perturbaciones y 24 / 48 réplicas |
| Proyecto | 16 384 / 32 768 frecuencias de dos puertos en SLPROJ |

La cancelación mide el intervalo desde la señal hasta el descarte cooperativo en una importación iniciada. El ensayo vuelve a abrir el archivo para comprobar recuperación. El Workbench mide arranque, primera apertura por herramienta, navegación entre documentos abiertos y render por separado. El perfil automatizado de Qt usa offscreen.
