# Avance 0.10 — espacio de estados y herramientas conectadas

## Alcance
Modelos continuos y discretos con matrices complejas A, B, C y D, varias entradas y salidas, estados iniciales y ganancias estáticas sin estados ficticios. Análisis numérico de controlabilidad, observabilidad y estabilidad interna. Conversión desde transferencias y extracción de un canal hacia transferencia. Los retardos y FIR digitales conservan la convención ascendente en z^-1. La realización compañera no elimina coeficientes pequeños por tolerancia.

Discretización ZOH, Tustin, Euler adelante y atrás. Simulación continua con entrada constante entre instantes (ZOH); simulación discreta por recurrencia. Respuesta frecuencial MIMO en rad/s: en digital z=exp(i*omega*T). Un sistema no mínimo puede producir una matriz singular aunque un canal reducido admita límite: esos puntos se indican como no disponibles; no se afirma una cancelación analítica.

Cada modelo, entrada, salida y estado se guarda con procedencia. Una señal del proyecto puede alimentar un modelo de una entrada. Las salidas se reutilizan en Fourier y otras herramientas. El esquema de proyecto 2 conserva dimensiones vacías de modelos estáticos y acepta proyectos anteriores de esquema 1. Versiones anteriores pueden rechazar el esquema nuevo. Una transferencia digital todavía no almacena su reloj: al convertirla se pide el periodo explícitamente.

## Interfaz
Inicio por tareas con buscador, menús directos y entradas propias. Reutilizar sistemas es opcional. Se corrigió la conservación de acciones del menú en PySide y se compactaron matrices; revisión visual offscreen a 1366×768. Los formularios largos se desplazan sin comprimir campos.

## Verificación
Pruebas de referencia analítica, recurrencia MIMO explícita, transferencias complejas, retardos, FIR, coeficientes pequeños, persistencia y rechazos de dimensiones/relojes inválidos en test_state_space.py. Flujos UI en test_toolbox.py: inicio sin señal, acceso por menú, salida de estados → Fourier y transferencia → estados → transferencia con procedencia. Registro completo: work/regression-0.10.txt. El autodiagnóstico portable ahora ejercita ToolboxWindow y espacio de estados, además de FFT, LTI, bilineal y runtime simbólico.

## Límites pendientes
Este bloque es numérico. Falta la representación matricial algebraica vinculada, condiciones simbólicas, reducción de modelos y auditoría general HP. Los rangos dependen del condicionamiento; la frontera de estabilidad requiere análisis adicional. Continúan vigentes todos los requisitos de OBJETIVO_LABORATORIO_PC.md.
