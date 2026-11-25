# Escalado y resolución

Cada captura indica plataforma Qt, DPI lógico, factor de escala, dimensiones lógicas de ventana y dimensiones físicas de cada PNG. Se incluye el límite 640 × 420 y 960 × 540 lógicos a 200 %, que aproxima 1920 × 1080 físicos. El perfil Xvfb tiene espacio para el mayor caso.

El factor `QT_SCALE_FACTOR` prueba el escalado de la aplicación. Los ajustes reales Windows por monitor y el escalado Wayland/X11 dependen del escritorio. Quedan pendientes las pruebas manuales que requieren esos entornos.

El monitor Windows de la revisión usa 1366 × 768 físicos y 96 DPI. Qt ajusta el tamaño de la ventana a esa superficie. Con factor 2 quedan 683 × 384 lógicos de pantalla, por debajo del alto mínimo de 420. Ese resultado marca el límite del entorno local para validar la ventana completa al 200 %.
