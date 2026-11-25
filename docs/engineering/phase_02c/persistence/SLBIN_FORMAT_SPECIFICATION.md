# SLBIN v1

| Campo | Representación |
| --- | --- |
| Identificador | Ocho bytes `SLPCBIN` seguidos de `0x01` |
| Tamaño de cabecera | `uint32` little-endian, 1 a 1 048 576 bytes |
| Cabecera | Objeto JSON UTF-8 con `count`, `origin`, `step`, `units`, `name`, `domain`, `expression`, `metadata` |
| Arreglo | `count` pares consecutivos real e imaginario, cada componente IEEE-754 binary64 little-endian |
| Integridad | 32 bytes SHA-256 del identificador, tamaño, cabecera y arreglo |

Se exige un archivo regular de tamaño exacto y `count` positivo. No se admiten claves JSON repetidas ni números no finitos. Un eje discreto preserva su origen entero y los otros ejes se ajustan al contrato de `Signal`. La lectura valida el archivo completo antes de entregar la señal. El submuestreo de lectura y el acceso por rango quedan fuera de la v1.
