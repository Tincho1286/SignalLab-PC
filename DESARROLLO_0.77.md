# SignalLab PC 0.77 · análisis en frecuencia dentro de la misma herramienta

27/10/2026. Desarrollo hacia 1.0; se conserva el escritorio oscuro y las siete áreas. El catálogo mantiene 31 problemas públicos y sus 72 variantes. No se agrega un menú Bode separado.

## Respuesta de H(s) y H(z)

Analizar un sistema incorpora distribución lineal o logarítmica de frecuencias. La logarítmica requiere frecuencias positivas y evalúa puntos por décadas; la lineal permite cero y frecuencias negativas. Las unidades siguen siendo rad/s o rad/muestra. En la barra de la figura se puede alternar módulo lineal/dB sobre los mismos datos, conservando el zoom horizontal. Módulo, fase y retardo comparten el eje de frecuencia.

El módulo usa 20 log10 |H|. Un cero exacto corresponde a −∞ dB y no se sustituye por un piso finito; fase y retardo no definidos quedan como tales. En un FIR de simetría exacta se presenta el retardo alrededor de su valor de fase lineal, evitando ampliar el ruido de redondeo como una gran variación aparente. Los datos calculados no se redondean ni se reemplazan para exportar.

La definición y el resultado usan un informe matemático con secciones. Las aclaraciones corresponden al dominio y al método de carga; una fórmula en s ya no recibe una explicación sobre potencias de z. Cambiar fórmula/coeficientes conserva el rango de frecuencia; cambiar dominio propone su límite habitual. Un resultado sólo algebraico muestra explícitamente que falta asignar parámetros para la figura numérica.

## Cruces y márgenes opcionales

Al activarlos, H se interpreta como L de lazo abierto con realimentación negativa unitaria y coeficientes reales. Se buscan cruces aislados |L|=1 y cruces por el eje real negativo dentro de la rejilla evaluada. Se refinan cambios de signo y mínimos locales muestreados; se valida el residuo para evitar confundir una singularidad con un cruce. Los márgenes de fase se expresan en radianes como distancia angular con signo en [−π,π). MG se informa como factor y dB.

El análisis es local al intervalo, no un certificado global. Puede omitir cruces entre puntos o fuera del rango. No encontrar cruces no significa margen infinito. Se informan los tramos críticos no aislados y candidatos no resueltos. Se excluye el cruce estático en frecuencia cero; en digital se usa la parte del intervalo incluida en 0…π. Coeficientes complejos o avances temporales conservan la respuesta en frecuencia, pero no reciben esta interpretación convencional de márgenes causales. Márgenes positivos por sí solos no certifican estabilidad del lazo cerrado.

## Exportación y ayuda

Exportar sistema guarda el modelo; Exportar respuesta guarda coordenadas, H real/imaginaria, módulo, dB, fase y retardo como CSV, o el análisis completo con todos los cruces detectados en JSON. Las coordenadas logarítmicas no se presentan como una señal de paso uniforme. Campos no definidos: vacíos CSV/null JSON; −∞ dB se conserva como -inf en CSV y se reconoce por módulo cero en JSON. La ayuda del mismo menú incorpora un dibujo coloreado de Bode, cruces y márgenes, junto con sus condiciones.

Se mantiene una única pestaña Polos y ceros y la reutilización del sistema en respuesta temporal, conversión y diseño. Estas capacidades no requieren reabrir un editor de diseño para consultar raíces.

## Evidencia dirigida

Ocho casos nuevos: rejilla logarítmica, márgenes de L=2/[s(s+1)(s+2)] frente a cruces analíticos, extremo de módulo cero, retardo digital y cruce en π, tangencia a ganancia unitaria, tramos unitarios no aislados, ausencia de cruces, coeficientes complejos/avance y exportación no uniforme con datos no definidos. Pasaron también cinco casos existentes de análisis algebraico.

Recorrido UI con el CAS real: fórmula → rejilla logarítmica y márgenes → informe → cambio a dB sin recalcular/perder zoom → exportación JSON → consulta de polos/ceros → ayuda ilustrada → FIR digital con retardo y frecuencias angulares. Se comprobó rechazo de inicio cero en log conservando el resultado anterior, parámetros simbólicos sin exportación numérica y documento a 800×600 y 640×480. Se revisaron capturas de informe, figura y ayuda. No se hizo una campaña general de regresión.

## Referencias de convenciones

- [SciPy: bode](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.bode.html): módulo en dB y frecuencia angular; la app conserva fase en radianes.
- [Python Control: stability_margins](https://python-control.readthedocs.io/en/stable/generated/control.stability_margins.html): definición de cruces/márgenes y alcance limitado cuando se parte de datos de frecuencia. Se consultó como referencia; no se agregó esa dependencia ni se copió su motor.
- [SciPy: brentq](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html): refinamiento de raíces en intervalos con cambio de signo.

Las carencias académicas restantes y los límites actuales siguen documentados en COBERTURA_SYS_I_II_ACTUAL.md y CIERRE_1.0.md. Esta compilación no declara completada la primera estable.
