# Engineering Core

```mermaid
flowchart LR
    Qt[Qt] --> App[Servicios de aplicación]
    Python[Python y CLI] --> App
    App --> Contexto[Contexto de ejecución]
    App --> Dominio[Signal y Transfer]
    App --> Motores[Motores científicos existentes]
    App --> Proyecto[Project y session]
    Motores --> Jobs[jobs]
    Jobs --> Contexto
```

La UI prepara datos y presenta resultados. La aplicación define contratos y coordina la ejecución. El dominio conserva modelos y unidades. Project y session controlan identidad y persistencia. Los motores conservan algoritmos y convenciones.
