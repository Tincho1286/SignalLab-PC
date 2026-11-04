"""Modelo de señal muestreada: datos y metadatos comparten un solo objeto."""

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class Signal:
    values: np.ndarray
    origin: float = 0.0
    step: float = 1.0
    units: str = "n"
    name: str = "x"
    domain: str = "discrete"
    expression: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.metadata,dict):raise ValueError('Los metadatos de la señal deben ser un diccionario.')
        self.values = np.asarray(self.values, dtype=np.complex128).reshape(-1).copy()
        if self.values.size == 0:
            raise ValueError("La señal debe contener al menos una muestra.")
        if not np.all(np.isfinite(self.values)):
            raise ValueError("Esta versión admite muestras finitas; N/D y estados especiales se están portando por separado.")
        if not np.isfinite(self.origin) or not np.isfinite(self.step) or self.step == 0:
            raise ValueError("El origen debe ser finito y el paso finito y distinto de cero.")
        if self.domain not in {"discrete","continuous","frequency"}:
            raise ValueError("El dominio debe ser discreto, continuo o de frecuencia.")
        if self.domain != "discrete" and self.values.size>1:
            first=float(self.origin);spacing=float(self.step);count=int(self.values.size)
            last=first+spacing*(count-1);previous=first+spacing*(count-2)
            if not np.isfinite(last):raise ValueError("El eje excede el rango numérico finito.")
            if first+spacing==first or last==previous:
                raise ValueError("El paso no permite distinguir coordenadas con este origen en doble precisión.")
        if self.domain == "discrete":
            try:
                integer_origin = int(self.origin)
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError("Una secuencia requiere un origen entero finito.") from exc
            if integer_origin != self.origin or self.step != 1:
                raise ValueError("Una secuencia usa índices enteros con paso 1.")
            limit = np.iinfo(np.int64)
            last_index = integer_origin + self.values.size - 1
            if integer_origin < limit.min or last_index > limit.max:
                raise ValueError("El eje excede el rango de índices enteros de 64 bits.")
            self.origin = integer_origin

    @property
    def data_kind(self):
        from .signal_semantics import signal_kind
        return signal_kind(self.domain,self.units,self.metadata)

    @property
    def axis(self) -> np.ndarray:
        if self.domain == "discrete":
            return np.arange(self.values.size, dtype=np.int64) + self.origin
        return self.origin + self.step * np.arange(self.values.size)

    def copy_with(self, *, values=None, origin=None, step=None, name=None, metadata=None, expression=None) -> "Signal":
        return Signal(
            self.values if values is None else values,
            self.origin if origin is None else origin,
            self.step if step is None else step,
            self.units,
            self.name if name is None else name,
            self.domain,
            self.expression if expression is None else expression,
            dict(self.metadata if metadata is None else metadata),
        )

