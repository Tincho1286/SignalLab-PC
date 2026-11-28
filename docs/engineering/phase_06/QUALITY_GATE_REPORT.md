# Quality Gate de Fase 06

**Aprobado** en Windows Server 2022 y Ubuntu 22.04 sobre `1eb462e24034a9c7f41183b4da4654334460d07c`. [Matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46094545163) · [Quality Gate completo](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.4.0/quality-gate-06.json)

| Plataforma | Pruebas integrales | Casos preventivos | Contrastes A–F | Líneas globales | Ramas globales |
| --- | ---: | ---: | ---: | ---: | ---: |
| Windows Server 2022 | 1508 | 150 | 32 | 90,28 % | 78,34 % |
| Ubuntu 22.04 | 1508 | 150 | 32 | 90,23 % | 78,33 % |

[Contrastes Windows](evidence/candidate-1eb462e/demonstrators/windows) · [Contrastes Ubuntu](evidence/candidate-1eb462e/demonstrators/linux)

## Componentes críticos RF y modernizados

| Plataforma | Módulo | Líneas | Ramas |
| --- | --- | ---: | ---: |
| Windows Server 2022 | rf_network.py | 100,00 % | 100,00 % |
| Windows Server 2022 | rf_analysis.py | 99,45 % | 98,00 % |
| Windows Server 2022 | rf_line.py | 97,99 % | 91,67 % |
| Windows Server 2022 | rf_matching.py | 96,45 % | 90,00 % |
| Windows Server 2022 | rf_link.py | 97,28 % | 100,00 % |
| Windows Server 2022 | rf_experiments.py | 100,00 % | 100,00 % |
| Windows Server 2022 | rf_storage.py | 98,53 % | 91,67 % |
| Windows Server 2022 | rf_application.py | 97,99 % | 95,83 % |
| Windows Server 2022 | rf_cli.py | 100,00 % | 100,00 % |
| Windows Server 2022 | touchstone.py | 96,68 % | 92,86 % |
| Windows Server 2022 | advanced_fourier.py | 97,86 % | 87,50 % |
| Windows Server 2022 | analog_design.py | 97,18 % | 85,19 % |
| Windows Server 2022 | window_signals.py | 98,97 % | 89,58 % |
| Windows Server 2022 | window_spectrum.py | 100,00 % | 94,44 % |
| Windows Server 2022 | project_archive.py | 96,32 % | 91,94 % |
| Ubuntu 22.04 | rf_network.py | 100,00 % | 100,00 % |
| Ubuntu 22.04 | rf_analysis.py | 99,45 % | 98,00 % |
| Ubuntu 22.04 | rf_line.py | 97,99 % | 91,67 % |
| Ubuntu 22.04 | rf_matching.py | 96,45 % | 90,00 % |
| Ubuntu 22.04 | rf_link.py | 97,28 % | 100,00 % |
| Ubuntu 22.04 | rf_experiments.py | 100,00 % | 100,00 % |
| Ubuntu 22.04 | rf_storage.py | 98,53 % | 91,67 % |
| Ubuntu 22.04 | rf_application.py | 97,99 % | 95,83 % |
| Ubuntu 22.04 | rf_cli.py | 100,00 % | 100,00 % |
| Ubuntu 22.04 | touchstone.py | 96,68 % | 92,86 % |
| Ubuntu 22.04 | advanced_fourier.py | 97,86 % | 87,50 % |
| Ubuntu 22.04 | analog_design.py | 97,18 % | 85,19 % |
| Ubuntu 22.04 | window_signals.py | 98,97 % | 89,58 % |
| Ubuntu 22.04 | window_spectrum.py | 100,00 % | 94,44 % |
| Ubuntu 22.04 | project_archive.py | 96,32 % | 91,94 % |

Los componentes críticos de fases anteriores figuran en el informe acumulado. El Gate aprobó los perfiles de recursos, la cancelación, los demostradores, la paridad de interfaces y los controles de los paquetes.

## Comparación con la Preview 2.3.1

Los informes enlazan métricas por módulo modificado y localizan líneas o ramas conservadas cuya ejecución cambió. [Windows](evidence/candidate-1eb462e/windows-coverage-comparison.json) · [Ubuntu](evidence/candidate-1eb462e/linux-coverage-comparison.json)

Los porcentajes bajaron para algunas métricas de `communications_storage`, `monte_carlo` y `window_signals` al agregar rutas. La comparación de los tres módulos confirma que las líneas y ramas conservadas que habían sido ejecutadas continuaron cubiertas en ambos sistemas. Las ramas de `window_signals` subieron de 68,75 % a 89,58 %.

## Distribución y binarios nativos

| Plataforma | CPython | Qt | Archivos nativos | Enlaces simbólicos |
| --- | --- | --- | ---: | ---: |
| Windows Server 2022 | 3.14.10 | 6.12.1 | 218 | 0 |
| Ubuntu 22.04 | 3.14.10 | 6.12.1 | 385 | 28 |

El inventario y el SBOM corresponden por SHA-256 a los portables distribuidos. Los comprobantes registran la biblioteca OpenSSL de `cryptography` y los controles nativos de actualización.

La publicación se verificó con SHA-256 y ambos canales firmados. [Publicación](evidence/candidate-1eb462e/publication.json) · [Comprobantes](evidence/candidate-1eb462e/verified-build.json)
