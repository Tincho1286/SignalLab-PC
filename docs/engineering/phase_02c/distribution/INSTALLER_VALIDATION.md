# Comprobación de instaladores

Windows ejercita el instalador real aislado, autodiagnóstico, rechazo de downgrade y borrado de lo instalado. Dos fixtures con identidad descartable prueban el reemplazo en el mismo directorio, el registro por usuario y la conservación de datos ajenos. Linux usa un hogar temporal, instala el archivo `.run`, ejecuta autodiagnóstico, repara la instalación y verifica la desinstalación con conservación de configuración y archivos ajenos.
