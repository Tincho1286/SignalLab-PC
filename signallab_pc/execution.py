"""Cooperative execution shared by the Qt-independent application services."""

from collections.abc import Callable
from dataclasses import dataclass
import math
from threading import Event
from time import monotonic

from . import jobs
from .resources import ResourceLimitError


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    max_work_bytes: int | None = None
    deadline: float | None = None
    cancel: Event | None = None
    progress: Callable[[int], None] | None = None

    def __post_init__(self):
        if self.max_work_bytes is not None and (
            type(self.max_work_bytes) is not int or self.max_work_bytes < 1
        ):
            raise ValueError('El presupuesto de memoria debe ser un entero positivo en bytes.')
        if self.deadline is not None and not math.isfinite(self.deadline):
            raise ValueError('El plazo monotónico debe ser finito.')

    def _check(self):
        if self.cancel is not None and self.cancel.is_set():
            raise jobs.OperationCancelled('Cálculo cancelado; se descartó el resultado.')
        if self.deadline is not None and monotonic() >= self.deadline:
            raise TimeoutError('Se agotó el plazo de ejecución.')

    def checkpoint(self, percentage=None):
        self._check()
        jobs.checkpoint(None if percentage is None else percentage / 100)
        if percentage is not None and self.progress is not None:
            self.progress(percentage)
        self._check()

    def require(self, estimate):
        self.checkpoint()
        if self.max_work_bytes is not None and estimate > self.max_work_bytes:
            raise ResourceLimitError(
                f'El cálculo estima {estimate} bytes de trabajo; el presupuesto es {self.max_work_bytes}.'
            )

    def run(self, function):
        def observe(fraction):
            self._check()
            if self.progress is not None and fraction is not None and 0 < fraction < 1:
                self.progress(min(99, max(1, int(fraction * 100))))
            self._check()

        self.checkpoint()
        with jobs.observe(observe):
            result = function()
        self.checkpoint()
        return result
