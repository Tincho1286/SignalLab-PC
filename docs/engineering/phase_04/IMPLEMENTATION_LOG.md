# Implementación de Fase 04

## Línea base y consolidación del multitrayecto

La base comprobada es `5a0bff926155f560fd6b071a010f422e587c8484`. El motor agrupaba tácitamente copias en la salida, sin una representación coherente que sirviera para calcular diagnósticos. Los taps del nuevo contrato son comunes al motor, el PDP, la normalización y la respuesta frecuencial. Los momentos usan retardos relativos para preservar la resolución con retardos compartidos grandes.

Validaciones en Windows con Python 3.14.10.

| Comando | Evidencia |
| --- | --- |
| `python -B -X utf8 -m unittest discover -s tests -p "test_communications_*.py"` | 75 pruebas aprobadas. Incluye `numpy.convolve`, `scipy.signal.freqz`, momentos exactos, normalización extrema, informe, reutilización y apertura de figuras. |
| `python -B -X utf8 tools/check_static.py` | Aprobado para 403 archivos Python. |
| `git diff --check` | Aprobado. |

La Fase 04 requiere repetir la calificación sobre el candidato definitivo Windows/Linux, junto con el alcance pendiente de la [matriz](TRACEABILITY_MATRIX.md).
