# Quality Gate de Fase 05

**Aprobado** para `bde8eaa10bdfb878c22f6dad0c5a93a5e6c932fe` en Windows Server 2022 y Ubuntu 22.04. Cero defectos P0 abiertos y cero P1 internos pendientes en el registro revisado. [Ejecución](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46059832440) · [Gate verificable](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.0/quality-gate-05.json)

## Cobertura e integridad

| Plataforma | Integrales | Preventivas | Líneas | Ramas | Línea base de Fase 04 |
| --- | --- | --- | --- | --- | --- |
| Windows Server 2022 | 1434 | 150 | 90,04 % | 77,69 % | 89,20 % / 76,28 % |
| Ubuntu 22.04 | 1434 | 150 | 89,99 % | 77,68 % | 89,14 % / 76,25 % |

Los objetivos son ≥85 % de líneas y ≥75 % de ramas globales por plataforma. Las líneas de componentes críticos deben alcanzar ≥90 % y sus ramas ≥85 %. Los recuentos de bloqueo se combinan sobre el denominador completo. Los bloqueos nativos se probaron entre procesos en ambas plataformas.

| Plataforma | Componente | Líneas | Ramas |
| --- | --- | --- | --- |
| Windows Server 2022 | sampling.py | 303/304 | 122/130 |
| Windows Server 2022 | fourier.py | 264/265 | 81/92 |
| Windows Server 2022 | execution.py | 83/83 | 26/26 |
| Windows Server 2022 | dft_application.py | 56/56 | 12/12 |
| Windows Server 2022 | dsp_application.py | 227/231 | 46/52 |
| Windows Server 2022 | dsp_pipeline.py | 129/134 | 21/22 |
| Windows Server 2022 | scientific_storage.py | 75/78 | 23/24 |
| Windows Server 2022 | project_archive.py | 102/107 | 41/46 |
| Windows Server 2022 | cas_worksheet.py | 59/59 | 42/42 |
| Windows Server 2022 | session_desktop.py | 334/348 | 138/154 |
| Windows Server 2022 | cli_session.py | 68/71 | 13/14 |
| Windows Server 2022 | operation_provenance.py | 54/57 | 19/22 |
| Windows Server 2022 | project.py | 289/299 | 128/146 |
| Windows Server 2022 | communications_data.py | 167/167 | 64/64 |
| Windows Server 2022 | communications_modulation.py | 206/206 | 59/60 |
| Windows Server 2022 | communications_pulses.py | 180/180 | 36/36 |
| Windows Server 2022 | communications_channel.py | 284/296 | 80/88 |
| Windows Server 2022 | communications_receiver.py | 176/176 | 46/46 |
| Windows Server 2022 | communications_metrics.py | 188/188 | 66/66 |
| Windows Server 2022 | communications_experiment.py | 238/245 | 74/80 |
| Windows Server 2022 | communications_storage.py | 179/183 | 52/56 |
| Windows Server 2022 | communications_sweep.py | 372/384 | 146/160 |
| Windows Server 2022 | communications_cli.py | 489/493 | 75/82 |
| Windows Server 2022 | communications_fading.py | 135/140 | 24/28 |
| Windows Server 2022 | communications_fading_distributions.py | 87/88 | 15/16 |
| Windows Server 2022 | communications_doppler.py | 153/157 | 26/30 |
| Windows Server 2022 | communications_impairments.py | 189/199 | 40/46 |
| Windows Server 2022 | communications_interference.py | 246/260 | 70/82 |
| Windows Server 2022 | communications_pipeline.py | 286/304 | 97/114 |
| Windows Server 2022 | communications_propagation.py | 115/120 | 29/32 |
| Windows Server 2022 | probability.py | 236/240 | 104/108 |
| Windows Server 2022 | multivariate_probability.py | 214/221 | 55/56 |
| Windows Server 2022 | probability_cli.py | 98/98 | 46/46 |
| Windows Server 2022 | descriptive_statistics.py | 128/128 | 36/36 |
| Windows Server 2022 | statistics_cli.py | 83/83 | 17/18 |
| Windows Server 2022 | statistical_inference.py | 336/344 | 143/148 |
| Windows Server 2022 | statistics_results.py | 23/23 | 8/8 |
| Windows Server 2022 | stochastic_processes.py | 295/298 | 99/102 |
| Windows Server 2022 | stochastic_cli.py | 332/341 | 73/82 |
| Windows Server 2022 | realization_batch.py | 17/17 | 6/6 |
| Windows Server 2022 | stochastic_noise.py | 223/226 | 87/90 |
| Windows Server 2022 | stochastic_covariance.py | 214/216 | 76/78 |
| Windows Server 2022 | ar_estimation.py | 199/211 | 73/82 |
| Windows Server 2022 | random_models.py | 256/268 | 76/86 |
| Windows Server 2022 | time_series_identification.py | 309/325 | 84/98 |
| Windows Server 2022 | statistical_spectra.py | 247/257 | 67/78 |
| Windows Server 2022 | optimal_estimation.py | 82/84 | 18/20 |
| Windows Server 2022 | wiener_filter.py | 128/131 | 27/30 |
| Windows Server 2022 | kalman_filter.py | 136/141 | 45/50 |
| Windows Server 2022 | adaptive_filter.py | 160/166 | 48/54 |
| Windows Server 2022 | monte_carlo.py | 307/313 | 105/110 |
| Windows Server 2022 | monte_carlo_bootstrap.py | 72/73 | 25/26 |
| Ubuntu 22.04 | sampling.py | 303/304 | 122/130 |
| Ubuntu 22.04 | fourier.py | 264/265 | 81/92 |
| Ubuntu 22.04 | execution.py | 83/83 | 26/26 |
| Ubuntu 22.04 | dft_application.py | 56/56 | 12/12 |
| Ubuntu 22.04 | dsp_application.py | 227/231 | 46/52 |
| Ubuntu 22.04 | dsp_pipeline.py | 129/134 | 21/22 |
| Ubuntu 22.04 | scientific_storage.py | 75/78 | 23/24 |
| Ubuntu 22.04 | project_archive.py | 102/107 | 41/46 |
| Ubuntu 22.04 | cas_worksheet.py | 59/59 | 42/42 |
| Ubuntu 22.04 | session_desktop.py | 334/348 | 138/154 |
| Ubuntu 22.04 | cli_session.py | 68/71 | 13/14 |
| Ubuntu 22.04 | operation_provenance.py | 54/57 | 19/22 |
| Ubuntu 22.04 | project.py | 289/299 | 128/146 |
| Ubuntu 22.04 | communications_data.py | 167/167 | 64/64 |
| Ubuntu 22.04 | communications_modulation.py | 206/206 | 59/60 |
| Ubuntu 22.04 | communications_pulses.py | 180/180 | 36/36 |
| Ubuntu 22.04 | communications_channel.py | 284/296 | 80/88 |
| Ubuntu 22.04 | communications_receiver.py | 176/176 | 46/46 |
| Ubuntu 22.04 | communications_metrics.py | 188/188 | 66/66 |
| Ubuntu 22.04 | communications_experiment.py | 238/245 | 74/80 |
| Ubuntu 22.04 | communications_storage.py | 179/183 | 52/56 |
| Ubuntu 22.04 | communications_sweep.py | 372/384 | 146/160 |
| Ubuntu 22.04 | communications_cli.py | 489/493 | 75/82 |
| Ubuntu 22.04 | communications_fading.py | 135/140 | 24/28 |
| Ubuntu 22.04 | communications_fading_distributions.py | 87/88 | 15/16 |
| Ubuntu 22.04 | communications_doppler.py | 153/157 | 26/30 |
| Ubuntu 22.04 | communications_impairments.py | 189/199 | 40/46 |
| Ubuntu 22.04 | communications_interference.py | 246/260 | 70/82 |
| Ubuntu 22.04 | communications_pipeline.py | 286/304 | 97/114 |
| Ubuntu 22.04 | communications_propagation.py | 115/120 | 29/32 |
| Ubuntu 22.04 | probability.py | 236/240 | 104/108 |
| Ubuntu 22.04 | multivariate_probability.py | 214/221 | 55/56 |
| Ubuntu 22.04 | probability_cli.py | 98/98 | 46/46 |
| Ubuntu 22.04 | descriptive_statistics.py | 128/128 | 36/36 |
| Ubuntu 22.04 | statistics_cli.py | 83/83 | 17/18 |
| Ubuntu 22.04 | statistical_inference.py | 336/344 | 143/148 |
| Ubuntu 22.04 | statistics_results.py | 23/23 | 8/8 |
| Ubuntu 22.04 | stochastic_processes.py | 295/298 | 99/102 |
| Ubuntu 22.04 | stochastic_cli.py | 332/341 | 73/82 |
| Ubuntu 22.04 | realization_batch.py | 17/17 | 6/6 |
| Ubuntu 22.04 | stochastic_noise.py | 223/226 | 87/90 |
| Ubuntu 22.04 | stochastic_covariance.py | 214/216 | 76/78 |
| Ubuntu 22.04 | ar_estimation.py | 199/211 | 73/82 |
| Ubuntu 22.04 | random_models.py | 256/268 | 76/86 |
| Ubuntu 22.04 | time_series_identification.py | 309/325 | 84/98 |
| Ubuntu 22.04 | statistical_spectra.py | 247/257 | 67/78 |
| Ubuntu 22.04 | optimal_estimation.py | 82/84 | 18/20 |
| Ubuntu 22.04 | wiener_filter.py | 128/131 | 27/30 |
| Ubuntu 22.04 | kalman_filter.py | 136/141 | 45/50 |
| Ubuntu 22.04 | adaptive_filter.py | 160/166 | 48/54 |
| Ubuntu 22.04 | monte_carlo.py | 307/313 | 105/110 |
| Ubuntu 22.04 | monte_carlo_bootstrap.py | 72/73 | 25/26 |
| Windows y Linux | campaign_files.py | 26/26 | 4/4 |

## Distribución y recursos

| Plataforma | Archivos SBOM | Salto desde LTS | Enlace nativo |
| --- | --- | --- | --- |
| Windows Server 2022 | 218 | Validado | Inventario nativo en el adjunto |
| Ubuntu 22.04 | 385 | Validado | Ubuntu libssl3 3.0.2-0ubuntu1.30 |

| Plataforma | Pico RSS de los perfiles | Mayor pausa de Qt offscreen | Máxima latencia cooperativa medida | Archivo de 262 144 muestras |
| --- | --- | --- | --- | --- |
| Windows Server 2022 | 132,88 MiB | 74,33 ms | 0,644 ms | 4 194 779 bytes |
| Ubuntu 22.04 | 152,21 MiB | 93,04 ms | 0,777 ms | 4 194 779 bytes |

La firma y la disponibilidad pública se verificaron después del Gate. La aceptación funcional y la integración quedan bajo control del propietario. [Dictámenes y descargas](PHASE_05_CLOSEOUT.md) · [Evidencia de procedencia](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.0/verified-build.json)
