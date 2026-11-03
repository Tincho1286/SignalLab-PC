# SignalLab PC 0.43 — Revisión transversal de entradas, ayuda y gráficos

- Las 76 rutas públicas tienen parámetros, esquema específico y explicación de lectura del resultado. Disponible en biblioteca y ayuda desplegable dentro de cada panel.
- Ayudas simbólicas corregidas para corresponder a controles reales: EDO, Z inversa derecha, Fourier algebraica y soporte de convolución/correlación.
- Explicación de la estimación Kaiser: mínimo de tolerancias y anchos de transición, cortes medios y comprobación posterior contra especificaciones originales.
- Campos numéricos reales/enteros unificados: expresiones constantes, coma decimal simple en escalares, rechazo de variables y mensajes asociados al campo. Las listas siguen separadas por coma, con punto decimal.
- Espectros manuales con selección rad/s o rad/muestra; filtros por tramos sincronizan esa unidad con su dominio.
- Señales temporales en parte real/imaginaria por defecto, conservando elección dentro del mismo dominio.
- PSD y densidad de energía reutilizadas se muestran como densidad y 10 log10, sin una fase ficticia.
- Fase principal continua sin líneas falsas en saltos de rama; muestras discretas conservan STEM.
- Plano de polos de estados con proporción igual; ejes compartidos en respuesta de sistemas y aviso de escala logarítmica.
- Reducción gráfica conserva extremos del módulo y extremos del eje; gráficos de respuesta con mayor altura útil.
- Esquemas de biblioteca se adaptan al ancho disponible.

Revisión estática de rutas, entradas y trazado, comprobación de cobertura 76/76 y sintaxis. Sin batería de pruebas funcionales/visuales: no se certifican todas las combinaciones numéricas. No se alteraron los métodos de diseño ni se forzó simetría en respuestas de filtros. Versiones anteriores conservadas.
