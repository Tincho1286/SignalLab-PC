# Versión 0.38

Implementado y empaquetado:
- Guardado común mediante archivo temporal en la misma carpeta, vaciado a disco y sustitución del destino al completar la escritura.
- Aplicado a sesiones, señales JSON/CSV, transferencias y reportes HTML/TXT.
- Ante errores de serialización o escritura previos a la sustitución, el archivo de destino anterior queda intacto.
- JSON rechaza valores no finitos; CSV comprueba que el eje sea finito.
- CSV escribe las coordenadas una por una, sin reservar una copia completa del eje.

Empaquetado completado correctamente y portable 0.38 copiado a la carpeta de entregas. Versiones anteriores conservadas. No se ejecutaron pruebas funcionales.
