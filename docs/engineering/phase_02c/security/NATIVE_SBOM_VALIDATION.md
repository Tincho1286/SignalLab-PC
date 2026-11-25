# SBOM de portables

El workflow construye el portable, inventaría PE y ELF, identifica origen por archivos equivalentes y comprueba las dos bibliotecas OpenSSL del paquete Ubuntu. Se preservan los avisos y licencias del empaquetador. Las bibliotecas embebidas y las aportadas por el anfitrión quedan fuera del alcance de un listado de archivos extraídos. [Inventario de partida](../../phase_02b/validation/phase02b-ci-8ad3066.json)

Para `459b9fc` se cotejaron los hashes y el origen de 219 binarios en Windows y 391 en Linux, además de 42 enlaces del portable Linux. Cada PE o ELF inventariado coincidió con un archivo de origen. El cruce con el manifiesto de licencias del repositorio encontró avisos con la misma versión para 12 paquetes por plataforma. Las bibliotecas Ubuntu se atribuyen a su paquete de sistema antes de empaquetar. Las dependencias de anfitrión que quedan fuera del portable y las bibliotecas estáticas requieren su propio seguimiento.

En Linux se confirmó `libssl.so.3` y `libcrypto.so.3` de Ubuntu `3.0.2-0ubuntu1.30`. En ambos portables el módulo de cryptography coincidió con el de la rueda que declara OpenSSL 4.0.3. [SBOM Windows](../validation/evidence/windows-native.cdx-459b9fc.json) · [SBOM Linux](../validation/evidence/linux-native.cdx-459b9fc.json) · [Aviso de Ubuntu](https://ubuntu.com/security/notices/USN-8847-1)
