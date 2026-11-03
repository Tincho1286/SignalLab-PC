# Alertas de Windows al descargar o abrir el portable

[← Documentación](README.md)

## Firma y reputación

El portable 1.2.0 se distribuye sin firma digital Authenticode. Windows puede mostrar «Windows protegió su PC» o un editor desconocido al abrir una descarga reciente. SmartScreen considera la identidad del editor y la reputación del archivo; una compilación nueva sin firma debe acumular su propia reputación. El canal estable de GitHub no sustituye esos mecanismos. [Microsoft: reputación de SmartScreen](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

Una firma de un editor de confianza identifica al publicador y permite mantener una identidad entre versiones. Firmar no garantiza que desaparezcan inmediatamente todos los avisos. La incorporación de firma de distribución permanece pendiente; su preparación y responsables se documentan en [Code signing policy](code-signing.md). [Microsoft: opciones de firma](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options).

## Distinguir el mensaje

Un aviso de aplicación no reconocida no equivale por sí solo a una detección de malware. Si Windows indica un nombre de amenaza o pone el archivo en cuarentena, se trata de una alerta diferente y debe analizarse su mensaje concreto. En Windows 11 también puede intervenir Smart App Control, según la configuración del equipo.

Las descargas oficiales están en [GitHub Releases](https://github.com/Tincho1286/SignalLab-PC/releases/latest). Los adjuntos incluyen un archivo SHA-256 para comparar la integridad de la descarga; un checksum no reemplaza una firma digital ni un análisis de seguridad.
