# Alertas de Windows al descargar o abrir el portable

[← Documentación](README.md)

## Firma y reputación

El portable y el instalador Windows 1.8.0 se distribuyen sin firma digital Authenticode. Windows puede mostrar «Windows protegió su PC» o un editor desconocido al abrir una descarga reciente. SmartScreen considera la identidad del editor y la reputación del archivo; una compilación nueva sin firma debe acumular su propia reputación. El canal estable de GitHub no sustituye esos mecanismos. [Microsoft: reputación de SmartScreen](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

Una firma de un editor de confianza identifica al publicador y permite mantener una identidad entre versiones. Firmar no garantiza que desaparezcan inmediatamente todos los avisos. La incorporación de firma de distribución permanece pendiente; su preparación y responsables se documentan en [Code signing policy](code-signing.md). [Microsoft: opciones de firma](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options).

## Distinguir el mensaje

Un aviso de aplicación no reconocida no equivale por sí solo a una detección de malware. Si Windows indica un nombre de amenaza o pone el archivo en cuarentena, se trata de una alerta diferente y debe analizarse su mensaje concreto. En Windows 11 también puede intervenir el Control inteligente de aplicaciones (Smart App Control), que evalúa confianza y firma y puede impedir por completo la ejecución. Actualmente no permite autorizar una excepción para una aplicación individual. Convertir un portable en instalador no cambia por sí solo esa evaluación. [Microsoft: Control inteligente de aplicaciones](https://support.microsoft.com/en-us/windows/security/threat-malware-protection/smart-app-control-frequently-asked-questions).

Las descargas oficiales están en [GitHub Releases](https://github.com/Tincho1286/SignalLab-PC/releases/latest). Los adjuntos incluyen un archivo SHA-256 para comparar la integridad de la descarga; un checksum no reemplaza una firma digital ni un análisis de seguridad.

La [firma de las actualizaciones](installed-updates.md) verifica la procedencia y los contenidos que instala SignalLab. Es independiente de la firma Authenticode que reconoce Windows.
