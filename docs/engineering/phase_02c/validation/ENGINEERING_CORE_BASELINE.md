# Línea base de Engineering Core 02C

| Referencia | SHA |
| --- | --- |
| Inicio de Fase 02C | `d29bcb8` |
| Línea base científica de Fase 02B | `8ad3066` |
| Candidato 02C | `459b9fc505c0a6a4d20bb6c5e898a5ae3f3cb281` |
| Estable distribuida | `v2.0.0` en `adfad5c` |

El candidato usa CPython 3.14.10 y Qt Essentials 6.12.0 en la matriz. El entorno fija dependencias, utiliza un hilo BLAS/OMP y separa suites instrumentadas, portables, instaladores, mediciones y capturas. Los detalles de cobertura, tamaños, tiempos y resultados nativos están en la [matriz final](FINAL_VALIDATION_MATRIX.md) y el [informe de la puerta de calidad](QUALITY_GATE_REPORT.md). [GitHub Actions](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45650373957)

El commit documental de cierre queda identificado por el commit que contiene este expediente y sus evidencias. `git log -1 --format=%H -- docs/engineering/phase_02c/closeout/PHASE_02C_CLOSEOUT.md` recupera esa revisión.
