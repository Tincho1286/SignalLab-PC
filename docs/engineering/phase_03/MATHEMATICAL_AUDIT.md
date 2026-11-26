# Auditoría matemática inicial

Se generaron referencias independientes antes de programar los motores. Para RC y RRC se integró el espectro ideal directamente, separando la meseta y la transición y usando su simetría par. Así se evalúan puntos incluso cuando la expresión temporal tiene una singularidad removible. Para BPSK se integró la cola gaussiana. Las etiquetas Gray se obtuvieron por reflexión recursiva y la energía de QAM cuadrada por suma explícita de niveles.

```sh
python tools/audit_communications_reference.py --output work/analytical-reference.json
```

Los vectores cubren roll-off 0, 0,2, 0,25, 0,5 y 1 y ambos lados de cada singularidad finita a una distancia de 10⁻⁷ períodos de símbolo. Se incluyen energías de 4, 16, 64 y 256-QAM y BER antipodal en cinco valores de Eb/N0. [Vectores](evidence/analytical-reference-v1.json) · [Convenciones](MATHEMATICAL_FOUNDATIONS.md)

La referencia QAM integra la gaussiana en todas las regiones de decisión de cada eje. Para BER pondera cada transición por la distancia de Hamming entre etiquetas Gray. Los 20 valores de SER coinciden con la fórmula de constelación cuadrada y los cinco de BER de 4-QAM coinciden con la integral antipodal. En 256-QAM a 0 dB, el BER exacto de referencia es 0,254607 y la aproximación por vecinos da 0,177892. Esta diferencia exige que el informe identifique la aproximación y su alcance. [Probabilidades de referencia](evidence/analytical-reference-v1.json)

Como contraste adicional se instaló Komm 0.37.0 únicamente en un directorio de auditoría con tqdm 4.67.3 y el NumPy del entorno fijado. En esa versión el RRC se obtiene con `RaisedCosinePulse(rolloff).root()`. Coincidieron el ciclo Gray de ocho etiquetas, las cuatro energías de QAM y RC en la grilla. RRC coincidió en los puntos ordinarios y en las singularidades con error absoluto de hasta 2,3 × 10⁻¹⁶. En la vecindad inmediata de los polos, la discrepancia de Komm llegó a 2 × 10⁻⁷. Esta comparación justifica usar la cuadratura como oráculo principal en esas vecindades. [Comparación](evidence/komm-comparison-v1.json) · [Modelo de pulsos](https://komm.dev/ref/RaisedCosinePulse/)

Con Komm instalado en un entorno de auditoría se reproduce la comparación mediante `python tools/audit_communications_reference.py --compare-komm --output work/komm-comparison.json`. Los experimentos Monte Carlo y las pruebas de recuperación, EVM y cancelación se incorporan al desarrollar sus contratos y servicios.

## Monte Carlo coherente

Cada configuración usó 90 000 símbolos equiprobables, semilla fija, AWGN y detección coherente, con una muestra por símbolo y sin ISI. En BPSK y QPSK Gray se contrastaron BER y SER mediante intervalos binomiales centrales de cobertura al menos 99,9 %. En 16-QAM se aplicó el mismo criterio a SER y se acotó la fracción de bits erróneos observada por símbolo con Hoeffding al 99,9 %. El control por unión de los diez contrastes da una probabilidad de falso rechazo de hasta 1 % bajo las hipótesis del ensayo. Todas las mediciones quedaron dentro de sus intervalos.

| Modulación | Eb/N₀ (dB) | Semilla | Errores / bits | Errores / símbolos |
| --- | ---: | ---: | ---: | ---: |
| BPSK | 0 | 191 | 7 018 / 90 000 | 7 018 / 90 000 |
| BPSK | 4 | 577 | 1 101 / 90 000 | 1 101 / 90 000 |
| QPSK Gray | 0 | 901 | 14 178 / 180 000 | 13 628 / 90 000 |
| QPSK Gray | 4 | 817 | 2 259 / 180 000 | 2 245 / 90 000 |
| 16-QAM Gray | 0 | 522 | 50 794 / 360 000 | 43 067 / 90 000 |

El laboratorio reporta incertidumbre binomial para observaciones independientes. Para BER de QAM de orden superior los bits de un mismo símbolo comparten la decisión. La cota del oráculo para este ensayo usa el símbolo como unidad independiente. Para RRC truncado, sincronización por piloto y datos manuales, el experimento informa los conteos y excluye la hipótesis binomial automática.

### Enlace QPSK sobre RRC truncado

Se contrastaron 32 transmisiones de 4 096 símbolos cada una, con semillas `40001` a `40032`, Eb/N₀ de 4 dB, ocho muestras por símbolo, roll-off 0,2 y span 6. Se obtuvieron los 49 coeficientes del RRC por cuadratura y se verificaron contra los que usó el enlace con error absoluto de hasta 2 × 10⁻¹⁴. La convolución directa con el filtro adaptado da la respuesta cada ocho muestras. Se aplicó esa respuesta a los símbolos obtenidos con la tabla Gray `00, 01, 11, 10` y rotación π/4.

La media sin ruido incluye la ISI de truncamiento. Para cada símbolo, si las probabilidades gaussianas de error en I y Q son $p_I$ y $p_Q$, el oráculo usa $(p_I+p_Q)/2$ para BER y $p_I+p_Q-p_Ip_Q$ para SER. La expectativa de EVM cuadrada se obtiene sumando la energía media del error de ISI y $N_0$ con energía de símbolos y filtro unitarias. El ancho de incertidumbre se estimó con diferencias apareadas por transmisión y un intervalo t aproximado al 99,8 % para cada cantidad.

| Medida | Media observada | Media de referencia | Semiancho sobre la diferencia |
| --- | ---: | ---: | ---: |
| BER | 0,0134773 | 0,0136086 | 0,0007198 |
| SER | 0,0268097 | 0,0270321 | 0,0014442 |
| EVM² | 0,2042972 | 0,2050158 | 0,0021052 |

Los tres intervalos contienen cero. La unidad de replicación es la transmisión completa. Los símbolos de un mismo registro comparten ruido filtrado e ISI, por lo que la app omite el intervalo binomial en ese perfil. [Resultados de las 32 réplicas](evidence/rrc-replicas-441f1c2.json)
