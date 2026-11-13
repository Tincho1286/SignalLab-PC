# Instalar y abrir SignalLab PC

[← Documentación](README.md)

La [última versión estable](https://github.com/Tincho1286/SignalLab-PC/releases/latest) ofrece instaladores y portables para Windows x64 y Linux x86_64. Todos incluyen Python y las dependencias de la aplicación. Elegí el formato según cómo quieras mantener el programa: el instalable registra accesos y permite actualizar desde SignalLab; el portable se ejecuta desde su carpeta.

## Windows x64

Para instalar la versión 1.8.8, descargá `SignalLab-PC-1.8.8-setup.exe` y abrilo. El instalador trabaja para tu usuario, por defecto en `%LOCALAPPDATA%\Programs\SignalLab PC`, y crea el acceso del menú Inicio. El acceso del escritorio es opcional. Las versiones siguientes pueden instalarse sobre la misma carpeta sin desinstalar previamente.

Si preferís la edición portable, descargá `SignalLab-PC-1.8.8.exe` y ejecutalo desde una carpeta donde tengas permisos. El instalador y el portable son archivos diferentes; el que termina en `-setup.exe` inicia la instalación.

Ambos ejecutables son de 64 bits. Windows puede mostrar avisos de editor desconocido o bloquear una descarga por su política de seguridad. La [guía de alertas de Windows](windows-downloads.md) distingue SmartScreen del Control inteligente de aplicaciones y explica la limitación actual de firma.

## Linux x86_64

Para instalar, descargá el archivo `.run` y ejecutá:

```sh
sh ./SignalLab-PC-1.8.8-linux-x86_64.run
```

La instalación se realiza para tu usuario, sin `sudo`, y agrega SignalLab al menú de aplicaciones. Para usar el portable, descargá el `.tar.gz`, descomprimilo y abrí `SignalLab-PC` dentro de la carpeta. La [guía de Linux](linux.md) incluye los comandos, la compatibilidad de glibc y los requisitos gráficos de ambos formatos.

## Primer inicio y configuración

Buscá una herramienta, completá sus entradas y presioná **Calcular**. No hace falta preparar una señal global antes de utilizar el laboratorio. **F1** abre la ayuda de la herramienta y **Ctrl+K** permite buscar operaciones; la [guía de primeros pasos](getting-started.md) muestra un ejemplo completo.

Los temas y las preferencias se guardan en los datos locales de tu usuario. Los resultados de trabajo deben exportarse cuando quieras conservarlos fuera de la sesión. [Importar y exportar datos](file-formats.md).

## Actualizar y desinstalar

En la edición instalada, abrí **Ayuda → Buscar actualizaciones**. La [guía de actualizaciones](installed-updates.md) describe la descarga verificada y el reinicio. La edición portable permite consultar las versiones y obtener otra descarga oficial, pero no reemplaza automáticamente su archivo.

En Windows, quitá la edición instalada desde la opción de desinstalación del sistema. En Linux, usá **Desinstalar SignalLab PC** en el acceso del menú o el comando indicado en la guía de actualizaciones. La desinstalación conserva la configuración y los documentos del usuario; los archivos administrados del programa se eliminan.
