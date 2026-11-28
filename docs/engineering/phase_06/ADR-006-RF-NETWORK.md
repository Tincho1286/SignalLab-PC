# ADR 006 · Red RF y cambio de base

## Decisión

Representar cada red mediante frecuencias explícitas y matrices complejas, con referencias reales positivas por puerto. Los puertos y unidades permanecen explícitos en el dato. Una red puede tener ganancia. ABCD describe únicamente cadenas de dos puertos con la convención de corriente definida en el contrato.

## Justificación

Las ecuaciones normalizadas de tensión y corriente permiten resolver el formato destino directamente. Este enfoque evita pasar por una matriz Z singular al convertir un paso ideal entre S y ABCD. Las referencias físicas complejas exigen elegir una definición de onda y comparadores que acrediten esa extensión. Su admisión queda para una decisión de alcance respaldada por casos.

El modelo RF tendrá esquemas de datos versionados y metadatos de procedencia. `Signal` y `Transfer` conservan contratos distintos y se reutilizan en los cálculos donde sus unidades y condiciones coinciden. Un valor escalar de transferencia aporta una relación entre señales. Las reflexiones y el resto de la matriz de red requieren un modelo adicional del circuito. [Contratos](SCIENTIFIC_CONTRACTS.md) · [Arquitectura](ARCHITECTURE.md)
