# Visión de SignalLab Engineering

SignalLab PC es un laboratorio de escritorio para estudiar señales y sistemas, comprobar cálculos y reproducir experimentos de ingeniería. El Workbench permite resolver una práctica con ayuda contextual e informes interpretables. Los mismos motores científicos pueden servir a flujos reproducibles en Python y en la consola cuando existe un contrato común.

## Expansión y modernización

Cada fase amplía el dominio científico y revisa las herramientas originales que ya intervienen en él. Se auditan las convenciones, las limitaciones y las rutas de reutilización antes de decidir qué ampliar. Los algoritmos que resuelven el mismo problema se integran como variantes en la herramienta correspondiente. Una herramienta independiente se justifica por el problema que permite resolver. [Roadmap](ROADMAP.md) · [Plan de modernización](TOOL_MODERNIZATION_PLAN.md)

Tras el cierre de Fase 05, el Core, las comunicaciones, los canales y la estadística sostienen la expansión analítica. SDR e instrumentación llegan en Fase 10 como última ampliación funcional. La Fase 11 califica el conjunto y prepara su mantenimiento a largo plazo. [Estado del proyecto](PROJECT_STATE.md) · [Dependencias científicas](ROADMAP.md#dependencias-científicas-entre-fases)

Las propuestas del roadmap definen una dirección científica. El alcance de implementación se concreta en los requisitos verificables de cada fase tras la autorización del propietario. Una decisión sustancial que altere ese alcance vuelve a revisión.

## Calidad de resultados

Los resultados conservan unidades, reloj, supuestos, dominio de validez, precisión, parámetros y procedencia. Las mediciones indican los límites del intervalo observado y los resultados estocásticos registran semillas, subflujos e incertidumbre. Los oráculos independientes contrastan la matemática y las regresiones protegen los proyectos y herramientas existentes. [Arquitectura objetivo](ARCHITECTURE_TO_BE.md) · [Criterios de calificación](VALIDATION_MATRIX.md#criterios-vigentes)

## Experiencia y distribución

La interfaz muestra los datos esenciales y deja a mano las opciones especializadas. Las hipótesis necesarias para interpretar un resultado siguen visibles. Qt y el Workbench actual son la base de esa evolución. [Principios de diseño](UX_DESIGN_PRINCIPLES.md)

Las fases calificadas se publican como Preview acumulativas. El propietario acepta el funcionamiento en sus equipos y autoriza por separado la integración y el inicio de la siguiente fase. Stable/LTS 2.0.x tiene su propio mantenimiento. [Política de entregas](RELEASE_POLICY.md)
