# Firma de las distribuciones

[← Documentación](README.md)

SignalLab distingue dos mecanismos: la firma de su canal de actualizaciones y la firma Authenticode que Windows utiliza para reconocer al publicador de un ejecutable. Sus finalidades y el estado actual de cada uno son diferentes.

## Canal de actualizaciones

Desde la edición instalada 1.8.0, el manifiesto de actualizaciones utiliza Ed25519. La aplicación distribuye la clave pública y verifica el manifiesto antes de utilizar sus direcciones, versión y hashes. La clave privada se conserva fuera del repositorio y se utiliza localmente para firmar la entrega, después de comprobar los instaladores de ambas plataformas.

La responsabilidad de mantenimiento, revisión y publicación corresponde a [Tincho1286](https://github.com/Tincho1286). Las contribuciones externas se revisan antes de incorporarse al código de distribución. La [guía técnica de firma](development/signing.md) explica los comprobantes y la identidad que debe mantenerse entre versiones.

## Ejecutables Windows

Los instaladores y portables publicados permanecen **sin firma Authenticode**. No hay un servicio de producción habilitado para obtenerla. La solicitud al programa gratuito de SignPath Foundation no fue aprobada; la presencia de una integración opcional en el código de construcción no implica disponer de una cuenta aprobada ni de un certificado.

Por eso, la firma Ed25519 del manifiesto no elimina un posible bloqueo de SmartScreen o del Control inteligente de aplicaciones. El formato instalable tampoco cambia por sí solo esa evaluación. La [guía de alertas de Windows](windows-downloads.md) explica la diferencia entre los mensajes y las limitaciones actuales.

## Código, construcción y alcance

Las distribuciones se generan desde un commit identificado del repositorio público mediante el [flujo de construcción](../.github/workflows/portable.yml). Los archivos de procedencia registran versión, origen e integridad; las acciones externas y las dependencias se fijan en la configuración de construcción.

Una futura distribución Authenticode solo podría anunciarse como firmada después de validar su certificado y el archivo recibido del proveedor. La configuración opcional permanece desactivada y falla si faltan sus credenciales; no marca un binario como firmado por haberlo construido.

Ninguna de estas firmas certifica la exactitud de todos los cálculos. Su función es vincular archivos a una identidad de distribución y detectar modificaciones; la interpretación matemática se documenta en los resultados y en la [guía de fiabilidad](mathematical-reliability.md).

[Instalación y actualizaciones](installed-updates.md) · [Privacidad](privacy.md)
