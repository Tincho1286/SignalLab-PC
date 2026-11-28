# Registro de implementación de Fase 06

## Línea base y decisiones iniciales

Se confirmaron las dos ramas oficiales, el cierre e integración de Fase 05, la etiqueta aceptada `v2.3.1`, el candidato `1311df1`, los controles de GitHub y las dos selecciones del actualizador firmado. Se identificaron el diseño analógico s, las medidas y ventanas de Fourier, la propagación reutilizable y los servicios de ejecución y persistencia. La primera frontera expresa una red en tensión y corriente normalizadas para permitir conversiones con referencias distintas sin intermediarios matemáticamente improcedentes. [Auditoría](AUDIT_AND_SCOPE_REPORT.md) · [Decisión](ADR-006-RF-NETWORK.md)

## Motores iniciales y almacenamiento

| Paquete | Implementación y evidencia local |
| --- | --- |
| WP-01 y WP-02 | Instantáneas inmutables. Conversión directa por resolución lineal y diagnóstico por frecuencia. Se cotejó paso directo con referencias desiguales, redes serie y derivación, límites abierto/corto, cascadas, terminación de un tercer puerto y retardo con un nulo de transmisión. |
| WP-03 | Línea uniforme con pérdidas, RLGC por frecuencia, coordenadas de Smith, síntesis L, cuarto de onda y stub. Se cotejaron fórmulas de impedancia de entrada, caso RLGC sin distorsión y balance de potencia de adaptadores ideales. |
| WP-04 | Bessel con orden y frecuencia, o por bandas con el mapeo fijado por la banda de paso. Se conserva la comparación anterior. Las tres normalizaciones se cotejaron con el polinomio Bessel de segundo orden y se comprobaron las transformaciones de bandas. |
| WP-05 | Balance de enlace usando propagación, Friis con temperatura física y ruido de entrada, y aproximación cúbica acotada. Se cotejó potencia de salida acumulada por etapa y proyección armónica de un modelo temporal independiente. |
| WP-06 | Zoom FFT y Chirp-Z, estimación de picos para tonos complejos aislados y cinco ventanas adicionales. Se cotejó la suma directa, el origen de muestras y el primer vector DPSS mediante la matriz de concentración espectral. |
| WP-08 | Touchstone 1.0/2.0 para S/Z/Y y registros RF versionados con huella. Se verificó ida y vuelta JSON/SLPROJ y cancelación de exportación antes del reemplazo atómico. |

Comandos locales en Windows con CPython del proyecto:

```text
python -B -X utf8 -m unittest -v test_rf_network test_rf_line_matching test_rf_link_bessel test_advanced_fourier test_touchstone_rf_storage
python -B -X utf8 -m unittest test_rf_link_bessel test_window_convolution_analysis test_measurement_views test_workbench_fourier_variants
```

Los controles de funciones y ventanas se ejecutaron con Qt fuera de pantalla. El candidato acumulado y los perfiles por plataforma quedan para la calificación del mismo SHA.

## Experimentos e interfaces

El barrido de adaptación mantiene fijos los componentes y evalúa cambios de carga o de elementos en toda la banda. La sensibilidad Bessel se estimó con diferencias centrales y se contrastó con derivadas cerradas. La incertidumbre de enlace convierte perturbaciones aditivas gaussianas en dB en escenarios del motor de campañas existente. La prueba interrumpe una campaña tras ocho réplicas y verifica que la reanudación reproduce las muestras y la huella de una ejecución independiente.

Se añadieron tres documentos RF y una variante de Fourier. Las rutas de redes importan o reutilizan matrices, muestran sus parámetros y permiten examinar Γ en la carta de Smith. El diseñador Bessel permanece en el diseñador analógico. Los resultados conservan las entradas y productos en el proyecto. La consola y el escritorio utilizan el mismo contrato de solicitud. [Ejemplos](RF_API_EXAMPLES.md)

El ensayo local de los demostradores A a F completó 32 comparaciones numéricas independientes. Se amplió la ejecución acumulativa de GitHub para retener sus evidencias y perfiles, verificar portables e instaladores y vincular el Quality Gate con el SHA de la publicación. [Validación](VALIDATION_MATRIX.md)

## Búsqueda de herramientas

La auditoría de distribución de `79901ce` detectó que la consulta «Z» también devolvía Chirp-Z. El índice consideraba una palabra de una letra como coincidencia parcial de un título. Se acotaron esos atajos a nombres y alias exactos. La prueba de búsqueda verifica «Z», «Z inversa», «Chirp-Z» y «CZT» desde el mismo índice que usa el Workbench. [Incidencia RF-05](tracked-findings.json) · [Ejecución del primer candidato](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46093246209)
