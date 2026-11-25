# Dependencias del Core

```mermaid
flowchart LR
    CLI[CLI] --> Apps[Servicios de aplicación]
    Python[API Python] --> Apps
    Qt[Qt · DFT piloto] --> Apps
    Apps --> Exec[Contexto y pool]
    Apps --> Domain[Signal, Transfer y motores]
    Apps --> Project[Proyecto y procedencia]
    CLI --> Session[Sesión]
    Session --> Project
    Project --> Domain
    CLI --> Binary[SLBIN experimental]
    Binary --> Domain
```

El grafo directo y transitivo se obtuvo del AST de los módulos incluidos. La prueba de importación ejecutó once entradas con un `MetaPathFinder` que rechaza las familias Qt. La ejecución agregó los seis registros esperados en un proyecto nuevo.
