# Privacidad de SignalLab PC

[← Documentación](README.md)

SignalLab PC calcula y representa señales y sistemas en el equipo donde se ejecuta. La aplicación no incorpora cuentas de usuario ni telemetría y no envía automáticamente señales, fórmulas, documentos o resultados a un servidor del proyecto.

## Datos del trabajo

Los archivos se importan y exportan mediante acciones de la persona que utiliza el programa. Los temas, las preferencias y las imágenes elegidas como fondo permanecen en los datos locales de su usuario. Compartir una captura o un informe mediante otro programa depende de la acción y de la configuración de ese programa.

Los diagnósticos de errores se guardan localmente y tienen tamaño limitado. Un aviso puede ofrecer copiar información para describir un problema, pero no la transmite por sí solo. Antes de publicar un diagnóstico, revisá que no incluya expresiones, rutas o datos que quieras mantener privados.

## Comprobación de actualizaciones

La edición instalada puede consultar las versiones estables de GitHub al iniciar. La opción se puede desactivar en **Ayuda → Buscar actualizaciones**. La solicitud de red incluye la versión de SignalLab y no contiene los datos de trabajo. Descargar e instalar una actualización requiere una acción del usuario.

El portable no comprueba novedades automáticamente, aunque permite realizar una consulta manual. Descargar paquetes, abrir enlaces o informar un problema en GitHub conecta con ese proveedor. Los mensajes y archivos adjuntos publicados en un repositorio público pueden ser visibles para otras personas.

## Construcción y firma

Las herramientas de desarrollo descargan dependencias al preparar el entorno y utilizan GitHub Actions para construir las distribuciones. Ese proceso trabaja con el código del repositorio, no con las señales y resultados de quienes usan la aplicación.

El manifiesto de actualizaciones se firma localmente. La clave privada no se sube a GitHub; se publica el manifiesto firmado y se distribuye la clave pública necesaria para verificarlo. La integración opcional de Authenticode no está habilitada como servicio de producción, por lo que no forma parte del uso habitual ni del canal de actualización actual. [Política de firma](code-signing.md).

Para las interacciones con GitHub se aplica también su [política de privacidad](https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement).
