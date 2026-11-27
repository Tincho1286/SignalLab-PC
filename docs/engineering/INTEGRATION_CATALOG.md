# Catálogo de integración científica

Las fases priorizan contratos y motores vigentes. Una dependencia externa se considera cuando el motor actual, un adaptador pequeño o una referencia independiente resultan insuficientes para un requisito ya aprobado. Los componentes de la última entrega y sus plataformas figuran en los inventarios de construcción. [Dependencias del proyecto](../development/dependencies.md) · [Fuentes de evaluación histórica](DEPENDENCY_AUDIT.md)

| Fase | Reutilización prevista | Dependencia o referencia por evaluar | Riesgo y evidencia pedida |
| --- | --- | --- | --- |
| 05 · Probabilidad y estadística | NumPy/SciPy, PCG64, motores AR/PSD, diagnósticos Rayleigh/Rician y campañas con semillas. | Distribuciones, estimadores y optimización de los runtimes existentes. Comparadores externos aislados solo si aportan un oráculo. | Colas, condicionamiento, error estadístico, sesgo por dependencia, versiones de RNG y semilla reproducible. Cuantiles, momentos, incertidumbre y ajuste contrastados con casos conocidos. |
| 06 · RF y microondas | Filtros analógicos, respuesta, FFT, análisis de ventanas y pérdidas de propagación. | Especificación Touchstone y una referencia o adaptador multipuerto independiente. | Impedancias por puerto, convenciones de ondas y matrices casi singulares. Intercambio verificado en ambas plataformas. |
| 07 · Punto fijo y DSP | `Encoding`, aritmética/SOS, muestreo, convolución y cambio racional. | Referencia entera y vectores de DSP, y modelos FPGA aislados cuando se justifiquen. | Exactitud de redondeo, signo, saturación, wrap, orden de operaciones y estados. Comparación bit a bit y costes por estructura. |
| 08 · Simulación y métodos numéricos | Editor LTI, estados, motores simbólicos, NumPy/SciPy y SymPy. | Solvers y modelos de referencia. Evaluar EDP y optimización avanzada mediante problemas y tolerancias previamente definidos. | Rigidez, ciclos algebraicos, cambios de reloj y errores de convergencia. Oráculos analíticos, error observado y límites reproducibles. |
| 09 · Plataforma integrada | Project, SLPROJ/SLBIN, API/CLI y biblioteca. | Notebooks mediante API y adaptadores de intercambio opcionales. | Pérdida de metadatos, incompatibilidad de esquemas y coste de proyectos grandes. Ensayos de ida y vuelta y recuperación. |
| 10 · SDR e instrumentación | I/Q con reloj, DSP por bloques, campañas, FFT/STFT/PSD, redes RF y modelos de canal. | SigMF y adaptadores de SoapySDR, RTL-SDR, PlutoSDR, USRP, SCPI/PyVISA según dispositivo y plataforma. | ABI y drivers, frecuencia/ganancia reales, límites de flujo y recursos. Pruebas con hardware representativo y arranque sin drivers. |
| 11 · Calificación | Instrumentación, métricas, oráculos, almacenamiento e infraestructura acumulada. | Mejoras de verificación justificadas por un defecto o brecha de evidencia. | Compatibilidad, contaminación de métricas y dependencias nativas. Reconciliar medición y evidencia reproducible de calidad. |

Los dispositivos y bibliotecas de evaluación son prospectivos. Su adopción requiere revisar licencia, avisos, mantenimiento, seguridad, precisión, compatibilidad con el CPython objetivo, distribución en Windows/Linux, memoria y coste de soporte. Los oráculos deben usar supuestos y convenciones verificables. Compartir biblioteca con la implementación puede servir como contraste, y requiere una referencia adicional para el comportamiento que se pretende calificar.

Los controles vigentes para E-04, importación MAT de confianza, integridad de archivos y límites por perfil conservan el alcance documentado. Toda ampliación de hardware, escritura, importación o presupuesto debe identificar sus riesgos y su evaluación antes de calificarse.

- [Comparadores de Comunicaciones](phase_03/INTEGRATION_CATALOG.md)
- [Referencias de Canales](phase_04/INTEGRATION_CATALOG.md)
- [Matriz de modernización](TOOL_MODERNIZATION_PLAN.md)
- [Arquitectura objetivo](ARCHITECTURE_TO_BE.md)
