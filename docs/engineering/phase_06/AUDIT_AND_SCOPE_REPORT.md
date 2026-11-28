# Auditoría inicial y alcance RF

Se contrastó el roadmap con las rutas públicas, los motores y el candidato aceptado. La búsqueda de Touchstone y conversiones multipuerto en el código de aplicación no encontró una frontera de red RF. Los siguientes activos sí tienen recorridos implementados. [Línea base](PHASE_06_BASELINE.md) · [Plan de modernización](../TOOL_MODERNIZATION_PLAN.md#fase-06--rf-y-microondas)

| Activo comprobado | Reutilización |
| --- | --- |
| `Transfer`, `analog_design`, `frequency_analysis`, `frequency_measurements`, `temporal_analysis` | Diseño de polos y respuesta en s, frecuencia, retardo, impulso y escalón. Ampliar la familia y las vistas existentes con Bessel y análisis paramétrico. |
| `Signal`, `dft_application`, `window_spectrum`, `spectral_measurements`, `statistical_spectra` | Mantener reloj, fases de origen, medidas de ventana y escala. `communications_doppler` usa `ZoomFFT` en un diagnóstico interno. DPSS existe en multitaper. Generalizar las variantes de uso interactivo bajo contratos explícitos. |
| `communications_propagation`, `communications_channel` | Reutilizar pérdida de espacio libre, log-distancia, sombra y convenciones de potencia. Conservar los supuestos de adaptación y temperatura del nuevo presupuesto. |
| `ExecutionContext`, `Project`, `session`, `project_archive`, `operation_provenance`, `monte_carlo` | Reservas estimadas, cancelación, escritores exclusivos, huellas, reanudación y lectura histórica. La red tiene una cuadrícula frecuencial explícita. |
| Workbench, selector de resultados y figuras | Incorporar redes y enlace RF por tarea. Mostrar Smith como vista de red/adaptación. Añadir Bessel, ventanas y transformadas a sus herramientas actuales. Preservar la preparación por documento. |

## Referencias y adopción

| Referencia | Uso decidido para la fase |
| --- | --- |
| NumPy y SciPy | Dependencias existentes. Resoluciones matriciales, raíces, diseño Bessel, CZT y ventanas se evalúan con sus versiones fijadas. Los resultados de la misma biblioteca no son el único oráculo. [NumPy](https://numpy.org/doc/stable/reference/routines.linalg.html) · [SciPy](https://docs.scipy.org/doc/scipy/reference/signal.html) |
| SymPy y mpmath | Referencias de prueba ya disponibles. Resolver ecuaciones de tensión y corriente y contrastar condiciones límite con precisión superior. [SymPy](https://docs.sympy.org/latest/tutorials/intro-tutorial/matrices.html) · [mpmath](https://mpmath.org/doc/current/) |
| scikit-rf | Comparador externo de convenciones, renormalización y resultados para un entorno de auditoría. No se requiere para instalar SignalLab. [Ondas y referencia compleja](https://scikit-rf.readthedocs.io/en/latest/examples/networktheory/Working%20with%20Complex%20Characteristic%20Impedances.html) |
| IBIS Touchstone | Especificación de interoperabilidad. Declarar subformatos, matriz y orden por versión. [Versión 2.0](https://ibis.org/touchstone_ver2.0/) · [Versión 2.1](https://www.ibis.org/touchstone_ver2.1/) |
| ngspice y Qucs-S | Comparación de circuitos lineales fuera del producto. Qucs-S sirve para observar convenciones de la interfaz y el backend. [ngspice](https://ngspice.sourceforge.io/docs/ngspice-manual.pdf) · [Qucs-S RF](https://qucs-s-help.readthedocs.io/en/latest/overview/simulation-types/rf.html) |
| openEMS | Referencia arquitectónica de otro dominio. Su motor FDTD trata simulación electromagnética tridimensional, fuera del alcance analítico de redes de esta fase. [Introducción a openEMS](https://docs.openems.de/en/latest/intro.html) |

La interoperabilidad se acredita con el subconjunto publicado, casos límite y errores explícitos. Se conservan los requisitos de licencia y empaquetado del lock actual. Los nuevos módulos científicos y adaptadores quedarán vinculados a casos trazables antes de calificar la Preview. [Contratos](SCIENTIFIC_CONTRACTS.md) · [Trazabilidad](TRACEABILITY_MATRIX.md)
