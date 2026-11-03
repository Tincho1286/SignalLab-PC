# Avance 0.6 — laboratorio conectado

Turno anterior: progreso verificable (EXE 0.5 y reorganización de menús). Este turno cambia la arquitectura para permitir reutilización, no da por logrado el objetivo completo.

## Evidencia actual
- Referencia HP: hash cotejado con la carpeta canónica; coincide con la referencia congelada.
- Proyecto tipado de señales, transferencias y cálculos: 3 pruebas unitarias aprobadas.
- Análisis algebraico/numérico: 5 pruebas aprobadas (fracciones, dominio digital, parámetros, denominador inválido, impulso causal).
- Recorrido Qt generar → desplazar → DTFT: padres de objetos y guardado comprobados.
- Recorrido Qt sistema b=[1/3], a=[1,1]: CAS aislado, fórmula original, proyección numérica y H(0)=1/3 comprobados.
- Evidencia de recorridos: work/project-preview/*.json; capturas en la misma carpeta.

## Auditoría de alcance
No completado: funciones HP pendientes en MATRIZ_MIGRACION.md, todas las rutas entre herramientas, estados especiales, análisis numérico/algebraico generalizado, opciones ampliadas PC, ayuda adaptada y protocolo bidireccional de capacidades. La importación de proyectos valida tipos y procedencia antes de incorporar objetos; no representa aún toda la sesión de widgets ni un formato de gran volumen optimizado.

Próximo trabajo: completar cobertura por capacidad HP, extender sistemas exactos y análisis continuo, homogeneizar informes/entradas/parámetros en el proyecto, agregar opciones PC y comprobar cada ruta. El objetivo original permanece activo.
