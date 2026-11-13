# SignalLab PC en Linux x86_64

[← Documentación](README.md)

La versión estable 1.8.1 ofrece un instalador `.run` y un portable `.tar.gz`. Ambos contienen la aplicación nativa, Python y las bibliotecas numéricas y de interfaz; no requieren Wine ni una instalación separada de Python. Comparten los motores y herramientas de la edición Windows.

## Instalación por usuario

Descargá el `.run` desde la [release estable](https://github.com/Tincho1286/SignalLab-PC/releases/latest) y ejecutá:

```sh
sh ./SignalLab-PC-1.8.1-linux-x86_64.run
```

El asistente instala para tu usuario sin `sudo`, crea el acceso del menú y prepara las siguientes actualizaciones desde **Ayuda → Buscar actualizaciones**. La ubicación predeterminada es `~/.local/share/SignalLab-PC/`; se respetan los directorios XDG configurados. La [guía de actualizaciones](installed-updates.md) explica la activación de versiones y la desinstalación.

## Edición portable

Si preferís ejecutar desde una carpeta, descargá el `.tar.gz`, descomprimilo y abrí el archivo `SignalLab-PC`:

```sh
tar -xzf SignalLab-PC-1.8.1-linux-x86_64.tar.gz
cd SignalLab-PC-1.8.1-linux-x86_64
./SignalLab-PC
```

El TAR conserva el permiso de ejecución. Si el gestor de archivos lo quitó, restauralo con `chmod u+x SignalLab-PC`. Tanto la carpeta elegida como el directorio temporal deben permitir ejecutar archivos: el empaquetado extrae temporalmente las bibliotecas al iniciarse.

## Compatibilidad y escritorio

La distribución se construye para procesadores Intel/AMD de 64 bits (`x86_64`), sobre Ubuntu 22.04 con glibc 2.35. Se dirige a sistemas con glibc 2.35 o posterior y bibliotecas gráficas compatibles. No incluye una compilación ARM ni Alpine/musl y no se presenta como un paquete universal para cualquier distribución.

Se necesita un escritorio gráfico con las bibliotecas del sistema utilizadas por Qt. X11 funciona mediante `xcb`; una sesión Wayland puede utilizar XWayland según su configuración. Si aparece un error de carga de `xcb`, revisá las dependencias gráficas del escritorio, entre ellas `libxcb-cursor0`, OpenGL/EGL, XKB y X11/XCB. Los [requisitos de Qt para X11](https://doc.qt.io/qt-6.10/linux-requirements.html) y las [condiciones de compatibilidad de PyInstaller](https://pyinstaller.org/en/stable/usage.html#making-gnu-linux-apps-forward-compatible) desarrollan esos requisitos.

## Archivos y procedencia

Los datos se guardan donde elijas al exportarlos y la configuración permanece en los datos locales de tu usuario. El portable contiene la GPL, los avisos del proyecto y `LICENSES/`, con los avisos comunes y los recogidos del entorno Linux en `linux-runtime/`.

`build-provenance.json` identifica la versión, el commit, la plataforma y el hash del ejecutable. Las Releases incluyen fuentes y checksums de los archivos distribuidos. Un checksum comprueba integridad; en la edición instalada, el [manifiesto firmado](installed-updates.md) verifica además el canal de actualización.

## Construir desde el código

Con Python 3.12 de 64 bits y los requisitos gráficos disponibles:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt -r requirements-quality.txt
bash build_portable_linux.sh
```

La construcción ejecuta los controles matemáticos, de código y de reutilización exigidos por el proyecto. Las salidas quedan en `outputs/`. El [flujo de GitHub Actions](https://github.com/Tincho1286/SignalLab-PC/actions/workflows/portable.yml) construye también el instalador y comprueba la instalación real con la aplicación empaquetada. [Guía de publicación](development/releases.md).
