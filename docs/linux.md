# SignalLab PC · portable Linux x86_64

El portable Linux incluye la aplicación, Python y las bibliotecas numéricas y de interfaz. No necesita un entorno Python instalado ni utiliza Wine. Se distribuye como `.tar.gz` con un ejecutable nativo ELF de 64 bits, documentación, licencias y el registro de construcción.

## Descargar y abrir

Descargá `SignalLab-PC-1.6.10-linux-x86_64.tar.gz` desde [SignalLab PC 1.6.10](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.6.10). Descomprimilo y abrí el ejecutable `SignalLab-PC` que está dentro de su carpeta. Desde una terminal:

```sh
tar -xzf SignalLab-PC-1.6.10-linux-x86_64.tar.gz
cd SignalLab-PC-1.6.10-linux-x86_64
./SignalLab-PC
```

El archivo TAR conserva el permiso de ejecución. Si el gestor de archivos lo eliminó, podés restaurarlo con `chmod u+x SignalLab-PC`. Usá una carpeta y un directorio temporal donde el sistema permita ejecutar archivos; el formato de un solo ejecutable extrae sus bibliotecas temporalmente al iniciarse.

## Compatibilidad

- Procesador Intel/AMD de 64 bits (`x86_64`); esta entrega no es para ARM/Raspberry Pi.
- Construcción en Ubuntu 22.04, con glibc 2.35. Se dirige a sistemas con glibc 2.35 o posterior y bibliotecas gráficas compatibles. No se presenta como una distribución universal para cualquier Linux; Alpine/musl no está incluido.
- Requiere un escritorio gráfico y las bibliotecas del sistema que utiliza Qt. X11 está soportado mediante el complemento `xcb`; una sesión Wayland puede utilizar XWayland según su configuración.
- Incluye las mismas herramientas y motores de cálculo que Windows. La interfaz se adapta a las fuentes y al escritorio disponibles en el sistema.

En un sistema Ubuntu/Debian mínimo que informe que no puede cargar el complemento `xcb`, pueden faltar bibliotecas gráficas del escritorio. El paquete `libxcb-cursor0` es uno de los requisitos de Qt; también se utilizan OpenGL/EGL, XKB y las bibliotecas X11/XCB. Las instrucciones y requisitos completos están en [Qt para X11](https://doc.qt.io/qt-6.10/linux-requirements.html). La compatibilidad de glibc sigue las [condiciones de distribución de PyInstaller](https://pyinstaller.org/en/stable/usage.html#making-gnu-linux-apps-forward-compatible).

## Archivos y licencia

Los datos y resultados se guardan donde elijas al exportarlos. La carpeta portable contiene `LICENSE`, `NOTICE.md`, `THIRD_PARTY_NOTICES.md` y `LICENSES/`; este último conserva tanto los avisos comunes del repositorio como los del entorno Linux en `linux-runtime/` y su manifiesto específico.

`build-provenance.json` identifica el commit, la versión, la plataforma y el checksum del ejecutable. El release publica checksums para verificar los archivos descargados y un archivo fuente específico de la construcción Linux. La firma Authenticode solicitada para Windows no se aplica al ELF Linux; un checksum comprueba integridad, no identidad del publicador.

## Compilar desde el código

En Linux x86_64, con Python 3.12 y las bibliotecas gráficas de Qt disponibles:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
bash build_portable_linux.sh
```

La distribución se genera en `outputs/`. El [flujo de GitHub Actions](https://github.com/Tincho1286/SignalLab-PC/actions/workflows/portable.yml) permite construir Windows y Linux juntos; las versiones siguientes conservan ambas plataformas por defecto. La compilación no ejecuta la aplicación ni pruebas de cálculo.

[Documentación](https://github.com/Tincho1286/SignalLab-PC/blob/main/docs/README.md) · [Código fuente](https://github.com/Tincho1286/SignalLab-PC)
