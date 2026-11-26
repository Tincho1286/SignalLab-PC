# Decisiones

## 25 de noviembre de 2026 · Despacho focalizado en Windows

La verificación de correcciones posteriores a `623c9dd` usa `desktop_regressions` en el flujo Mathematical reliability. Esta opción ejecuta en `develop` los tres casos de escritorio identificados. Un reintento del trabajo histórico usaría el SHA original. El despacho focalizado registra el SHA corregido y conserva la matriz integral y sus controles como evidencia independiente. [Ejecución focalizada](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45744295852)

## 25 de noviembre de 2026 · Un candidato y evidencia de escritorio separada

La proyección focal orientó la selección de `623c9dd`. La medición integral local de ese SHA en Windows confirmó 88,39 % de líneas y 75,20 % de ramas y habilitó un único despacho de la matriz. El hallazgo posterior de cambio de tamaño se corrige en un commit separado de `develop`. La corrida y sus artefactos siguen correspondiendo al candidato inmutable. [Matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45739704501) · [Acta de escritorio](gui/DESKTOP_CONTINUATION.md#medidas-de-frecuencia-en-el-candidato-623c9dd)

## 25 de noviembre de 2026 · Publicación y recuperación por sesión

La entrada capturada para una operación LTI se publica al aceptar su resultado. Publicarla al validar el formulario dejaba objetos huérfanos si el motor rechazaba el sistema o si el usuario cancelaba. El checkpoint automático pertenece a la generación de la sesión en que se tomó la instantánea. Un cambio confirmado invalida una escritura propia anterior cuando termina. Se preservan los respaldos de otras instancias y los que el usuario decide conservar. Se reutilizan la entrega de resultados del escritorio y la escritura atómica existente. [Regresiones y comandos](IMPLEMENTATION_LOG.md)

## Continuidad de 02C · 25/11/2026

- E-01 y E-02. Mantener ruedas fijadas mientras el proveedor no entregue una corrección utilizable y reproducible. Aislar el lector nativo MATLAB antes de importar SciPy o h5py y delimitar su uso a archivos seleccionados localmente.
- E-03. Aplicar la cuota del SO al lector MAT y conservar la reserva estimada y la cancelación cooperativa para los motores numéricos. El banco mide archivos y operaciones concretas. La latencia observada no fija un plazo máximo.
- C-06. Mantener JSON y añadir `.slproj` opcional. Almacenar cargas complejas en binario en un solo archivo atómico. Conservar resultados CAS publicados y explicitar el alcance de variables y borradores activos.
- E-04. Usar 2.0.1 como versión de auditoría en develop. Verificar la actualización desde 2.0.0 con un entorno descartable y una clave de ensayo. Mantener la firma para distribución pública como condición independiente.
- E-05 y E-06. Conservar los objetivos y el alcance de instrumentación. Registrar escritorio real por separado de los perfiles automatizados y dirigir las nuevas pruebas a flujos con resultados observables.

## Decisiones registradas en el expediente anterior

- WP11. Mantener separados los dictámenes del Core, de arquitectura y de distribución y solicitar la aceptación de cada excepción.

- WP10. Mantener motores y fronteras actuales sin introducir una reorganización transversal.

- WP09. Separar el transporte verificado del candidato de la distribución pública y del salto por versión.

- WP08. Distinguir inspección en escritorio y evidencia automatizada de tamaño y escala.

- WP07. Registrar medianas y RSS sin introducir umbrales temporales frágiles en runners compartidos.

- WP06. Conservar pruebas con efectos observables y registrar cada déficit de cobertura por componente.

- WP05. Mantener JSON para proyectos y SLBIN experimental con especificación formal.

- WP04. Mantener cancelación cooperativa y evitar completar una escritura descartada cuando el CLI ya conoce el estado.

- WP03. Conservar huellas acotadas por bloque y evidencia opcional compatible con sesiones históricas.

- WP02. Construir el eje de PSD a partir de Fs y N, sin invertir un período fuera de rango.

- WP01. Restringir entradas a datos locales y verificar formatos antes del decoder.

- WP00. Conservar evidencia histórica y establecer una referencia reproducible de código.
- WP01. Pendiente de verificar rutas y dependencias.
- WP03. El criterio es comprobar contenido científico antes de publicar.

## Continuidad autónoma 02C

- C-05. Usar un presupuesto estimado compartido por defecto en las fronteras de aplicación y en la persistencia binaria. Mantener la cuota efectiva del lector MAT y reservar su capacidad antes de crearlo. El pool integra consumidores del proceso, con margen del host o cgroup. El proceso simbólico es terminable y sigue sin cuota propia.
- C-06. Recuperar de forma automática con un escritor y una instantánea de catálogo en SLPROJ. Mantener el diálogo y el formato predeterminado JSON para guardado explícito. Mantener lectura de checkpoints JSON anteriores.
- C-06. Verificar el volumen de comunicaciones con proyectos independientes y catálogo. El banco usa señales sintéticas y vuelve a cargar cada proyecto. Controlar el consumo al retener una ejecución a la vez.
- C-11. Calcular el gate desde las evidencias de dos sistemas con la misma revisión. La aceptación de riesgos y las actas externas requieren revisión explícita. El comando con `--require-automated` devuelve error cuando falte un requisito automático.

## Revisión de a80508c

- C-01 y C-02. Conservar los pines de la matriz. La revisión de proveedores identifica cuándo actualizar las dependencias y volver a cotejar los binarios que las contienen. [Consulta e inventario](security/DEPENDENCY_CONTINUATION.md#consulta-de-proveedores-para-a80508c)
- C-08. Acreditar los perfiles realmente ejecutados en Windows a 100 % y 125 %. Los perfiles de Xvfb siguen siendo evidencia automatizada. E-05 queda abierto para los perfiles restantes. [Acta](gui/DESKTOP_CONTINUATION.md#acta-windows-del-candidato-a80508c)
- C-11. Usar la corrida 45745729541 para el candidato y un commit documental posterior para el expediente. Los resultados acreditan el gate automático. El cierre del Core, la preparación de Fase 03 y la distribución pública se evalúan por separado. [Dictámenes](validation/QUALITY_GATE_REPORT.md#evaluación-del-candidato-a80508c)

## Aprobaciones del 26 de noviembre de 2026

- E-02 y E-03. El mantenedor aprobó la importación MAT para archivos confiables y la envolvente operativa de los perfiles probados.
- E-05. El mantenedor informó pruebas Windows al 150 % y 200 % y aprobó el alcance de Windows. Queda pendiente el acta de Linux real.

[Alcance de las aprobaciones](validation/EXCEPTION_APPROVAL_REGISTER.md#aprobaciones-del-mantenedor-del-26-de-noviembre-de-2026)

## Resolución técnica de E-01

Se adoptó Qt 6.12.1 desde el lote oficial fijado y se excluyó el decodificador JPEG 2000 al compilar Pillow. Las dos plataformas acreditaron la versión y los componentes efectivos mediante el ejecutable instalado y el SBOM. [Evidencia y alcance](security/DEPENDENCY_CONTINUATION.md#verificación-de-e-01-en-64dc3c4)

## Aprobación de E-05 y cierre del Core

El mantenedor informó sus pruebas manuales en otro escritorio Linux y aprobó E-05 en Linux el 26/11/2026. La aceptación completa los requisitos de escritorio del cierre técnico. La repetición independiente queda disponible con acceso al escritorio Linux. El inicio de Fase 03 y la distribución conservan decisiones propias. [Aprobación](validation/EXCEPTION_APPROVAL_REGISTER.md#resolución-de-e-05) · [Dictamen](validation/QUALITY_GATE_REPORT.md#cierre-técnico-de-fase-02c)

## Política de distribución y E-04

El 26/11/2026 el mantenedor ratificó el flujo de distribución vigente de `main` y dejó E-04 abierto como seguimiento sin bloqueo de entregas. La guía de publicación establece los controles de cada entrega, incluido el manifiesto firmado para instaladores. [Registro de E-04](validation/EXCEPTION_APPROVAL_REGISTER.md#seguimiento-de-e-04) · [Guía de publicación](../../development/releases.md)
