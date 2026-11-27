# Deuda técnica y límites de Fase 05

| Área | Límite documentado | Condición para ampliarlo |
| --- | --- | --- |
| PSD | Los intervalos χ² disponibles se califican para potencia de ruido blanco gaussiano en bloques rectangulares disjuntos. | Estimar grados de libertad y cobertura con oráculos por estimador antes de ofrecer intervalos de superposición, multitaper o espectros cruzados. |
| Procesos gaussianos | Las simulaciones exactas cubren Wiener, Ornstein–Uhlenbeck y modelos ARMA gaussianos estacionarios. La normal multivariada cubre observaciones con covarianza dada en una rejilla finita. | Ampliar a kernels temporales adicionales solo con método, admisión de recursos y evidencia de calibración propios. |
| Kalman | El alcance calificado es lineal y discreto, con covarianzas por factores y componentes ausentes. | EKF requiere linealizaciones verificadas cerca de la trayectoria. UKF requiere validar la propagación de momentos y su sensibilidad a escalas. Un filtro de partículas requiere controles de degeneración y reproducibilidad. Los tres necesitan autorización y oráculos propios. |
| Campañas | El bloqueo del catálogo se prueba entre procesos en disco local y la memoria se admite por estimación. | Calificar semántica de bloqueo y recuperación en un sistema de archivos compartido antes de incluirlo en el perfil. |
| Escritorio físico | Las pruebas automatizadas verifican interacción y latencia con Qt offscreen. | Registrar la experiencia de la Preview en configuraciones de pantalla reales durante la aceptación funcional. |
| Distribución | Authenticode continúa como seguimiento independiente. El manifiesto de actualización Ed25519 identifica canal, instaladores y huellas. | Mantener la decisión de canal y firma de ejecutables bajo la política de distribución vigente. |

[Riesgos y mitigaciones](SECURITY_REVIEW.md) · [Evidencia de rendimiento](PERFORMANCE_REPORT.md)
