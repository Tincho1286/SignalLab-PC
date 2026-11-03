# Operation Health

Operation Health es una revisión de robustez en entregas preliminares. Se priorizan resultados matemáticos coherentes, transferencia de datos entre herramientas, acciones de interfaz que respondan y diagnósticos útiles cuando una operación falla. La aceptación de uso y visual de cada preview corresponde a las pruebas del usuario; los controles automáticos básicos evitan distribuir fallos ya reproducidos.

## Cómo se entrega cada preview

Cada entrega publica portables de Windows y Linux, fuentes y notas con cuatro apartados: errores corregidos, fallos que se busca prevenir, casos que puede probar el usuario y pendientes conocidos. Cada caso manual indica el menú, los datos, la acción y el resultado esperado. No se publica una corrección como confirmada cuando sólo hay una sospecha. Las medidas preventivas describen su cobertura, sin prometer ausencia de errores futuros.

## Registro de hallazgos

| ID | Hallazgo y evidencia | Estado |
|---|---|---|
| OH-001 | H(w)=step(pi/2-abs(w))*exp(-4*i*w) generaba NameError al intentar evaluar DiracDelta como retardo ordinario. | Corregido en 1.5.6-preview; aceptación manual pendiente. |
| OH-002 | Una excepción de una acción Qt fuera del cálculo sólo llegaba al manejador de Python; el portable sin consola podía parecer inactivo. Reproducido con un botón real. | Diagnóstico visible en 1.5.6-preview. |
| OH-003 | Si fallaba la presentación del resultado, la barra seguía mostrando el mensaje del cálculo. Reproducido invocando la recepción real de un resultado. | Corregido en 1.5.6-preview. |
| OH-004 | Los fallos del proceso de trabajo sólo enviaban str(error), perdiendo tipo y ubicación de la excepción. | Corregido en 1.5.6-preview; diagnóstico local con tamaño limitado. |
| OH-005 | Una importación local condicional puede ocultar un nombre importado por el módulo y romper otro recorrido del mismo botón, como ocurrió en Graficar resultado. | Prevención añadida en 1.5.6-preview: análisis estático y controles de acciones Qt. No es un análisis completo de todos los caminos posibles. |
| OH-006 | DTFT algebraica exige condición=True para habilitar Graficar; una DTFT convergente salvo en frecuencias concretas queda bloqueada por completo. Evidencia: condiciones de convergencia válidas y bloqueo explícito del botón. | Pendiente para la siguiente tanda. |

## Siguientes tandas

1. Condiciones y reutilización: muestreo de resultados condicionados, conservación de soporte, unidades y restricciones al copiar, exportar, importar y enviar al CAS. Revisar entradas editadas frente al último resultado calculado.
2. Escalas y datos numéricos: bordes, ceros, polos, muestras grandes o pequeñas, pasos de ejes y coincidencia entre datos, tabla, cursor y exportación. Revisar CSV/JSON/MATLAB y errores de entrada sin modificar resultados anteriores.
3. Recorrido de herramientas: abrir las opciones públicas, comprobar sus acciones principales y registrar qué variantes quedan cubiertas. Añadir una regresión cuando se confirme una familia nueva de fallos.

Estas tandas son objetivos de revisión, no funcionalidades nuevas. Los problemas confirmados que afectan resultados tienen prioridad sobre mejoras visuales. Una preview no se convierte en estable sólo por superar los controles automáticos.

## Diagnósticos

Los errores inesperados permiten copiar un diagnóstico con referencia, versión, plataforma, acción y traza. Se guarda localmente en la carpeta de datos de SignalLab; el cuadro indica la ruta. Los archivos rotan con un máximo aproximado de 1,5 MiB. No se transmiten automáticamente. Los errores normales de datos conservan sus mensajes de validación cuando la herramienta ya los gestiona.
