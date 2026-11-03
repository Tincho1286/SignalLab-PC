# Compilar y publicar versiones

[← Desarrollo](README.md)

Desde 1.2.1, cada nueva entrega debe publicar portables para **Windows x86_64 y Linux x86_64**, con sus fuentes y checksums. La elección de una sola plataforma en el flujo sirve para reconstruir o incorporar esa plataforma a una entrega existente.

## Compilar el portable

Desde la raíz del proyecto, con el entorno preparado:

```powershell
.\build_portable.ps1 -Name SignalLab-PC-1.2.1
```

El resultado se guarda en `outputs/`. La compilación usa un directorio intermedio y reemplaza el archivo de salida al terminar, para conservar las copias de versiones anteriores. `-KeepBuildFiles` permite conservar los intermedios para diagnóstico.

Las siguientes compilaciones incluyen la licencia del proyecto y los avisos originales de terceros dentro del portable. En Releases se publica también el código fuente correspondiente y una copia accesible de esos avisos. Una actualización de licencia y documentación puede acompañar un portable existente sin alterar su ejecutable.

## Portable Linux

`build_portable_linux.sh` usa `.venv/bin/python` y genera un ejecutable nativo x86_64 en un paquete `.tar.gz`, con licencias y procedencia. Se construye en Linux; PyInstaller no convierte el ejecutable Windows en un ELF. El flujo de GitHub permite elegir `both`, `windows` o `linux` y tiene ambas plataformas como valor por defecto. La solicitud de firma sólo afecta al trabajo Windows.

[Uso y construcción en Linux](../linux.md). Para incorporar otra plataforma a una versión ya publicada se adjuntan su binario, fuente, procedencia y checksums; se conserva el ejecutable Windows y la etiqueta original. El commit de cada plataforma queda identificado por separado.

## Notas de publicación

Las notas describen el comportamiento de la versión: funciones incorporadas, correcciones, compatibilidad y límites conocidos. El catálogo está en [docs/releases/catalog.json](../releases/catalog.json); las páginas de versión se encuentran en [Notas de versiones](../releases/README.md).

Las versiones estables y las preliminares se distinguen mediante los indicadores de GitHub. Una publicación de documentación no necesita generar un nuevo ejecutable.

## Subir una versión

Guardá el código y las notas en un commit y subí `main`. Después, publicá el ejecutable y la documentación correspondiente:

```powershell
.\.venv\Scripts\python.exe -B tools\github_release.py `
  --tag v1.2.1 `
  --title "SignalLab PC 1.2.1 · Transferencias H(s)/H(z)" `
  --notes docs\releases\v1.2.1.md `
  --file outputs\SignalLab-PC-1.2.1.exe `
  --file outputs\SignalLab-PC-1.2.1-linux-x86_64.tar.gz `
  --stable `
  --allow-public
```

Por defecto se crea una preliminar. `--stable` identifica una entrega estable y `--allow-public` habilita la publicación en el repositorio público configurado. La herramienta utiliza la sesión de Git existente, comprueba la coincidencia con `main` y verifica la integridad de los adjuntos.

## Conservar el historial

Los ejecutables se distribuyen en Releases y no forman parte del historial Git. Las etiquetas identifican el código de cada versión. Las actualizaciones editoriales de una publicación conservan la etiqueta, la fecha, el estado y el ejecutable; si cambia un documento adjunto, su checksum se actualiza junto con él.

## Fechas y orden de Releases

GitHub ordena el listado usando la fecha de la etiqueta o del commit, que puede diferir de la fecha de publicación. Marcar una versión como Latest controla la descarga principal, pero no corrige por sí solo fechas de referencia adelantadas.

El publicador crea las etiquetas nuevas como anotadas, con la fecha UTC informada por GitHub. Conserva el commit exacto de construcción y comprueba el destino de cualquier etiqueta que ya exista, sin reemplazarla. Así la fecha local del equipo no desplaza el orden de las nuevas entregas.

Las etiquetas v1.2.0-preview, v1.2.0 y v1.2.1 se normalizaron con sus fechas originales de publicación. Conservan sus mismos commits, contenidos y archivos descargables. Al actualizar una copia local antigua de esas etiquetas, puede ser necesario volver a obtener sus metadatos con un fetch explícito; no requiere recompilar los portables.
