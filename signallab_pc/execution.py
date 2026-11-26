"""Cooperative execution shared by the Qt-independent application services."""

from collections.abc import Callable
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field, replace
import math
from threading import Event, Lock
from time import monotonic

from . import jobs
from .resources import ResourceLimitError, available_physical_memory


class ResourcePool:
    """Shared admission budget for estimates of concurrent working memory."""

    def __init__(self, capacity_bytes: int | Callable[[], int]):
        if not callable(capacity_bytes) and (type(capacity_bytes) is not int or capacity_bytes < 1):
            raise ValueError('La capacidad debe ser positiva y expresada en bytes enteros.')
        self._capacity = capacity_bytes
        self._used = 0
        self._lock = Lock()

    @contextmanager
    def reserve(self, amount):
        if type(amount) is not int or amount < 0:
            raise ValueError('La reserva requiere bytes enteros no negativos.')
        with self._lock:
            capacity = self._capacity() if callable(self._capacity) else self._capacity
            if amount > max(0, capacity - self._used):
                raise ResourceLimitError('La reserva compartida está ocupada o es insuficiente.')
            self._used += amount
        try:
            yield
        finally:
            with self._lock:
                self._used -= amount


_PROCESS_POOL = ResourcePool(lambda: int(.35 * available_physical_memory()))


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    max_work_bytes: int | None = None
    deadline: float | None = None
    cancel: Event | None = None
    progress: Callable[[int], None] | None = None
    pool: ResourcePool | None = field(default_factory=lambda: _PROCESS_POOL)

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
        if type(estimate) is not int or estimate < 0:
            raise ValueError('La estimación debe expresarse en bytes enteros no negativos.')
        if self.max_work_bytes is not None and estimate > self.max_work_bytes:
            raise ResourceLimitError(
                f'El cálculo estima {estimate} bytes de trabajo; el presupuesto es {self.max_work_bytes}.'
            )

    def reserve(self, estimate):
        self.require(estimate)
        return self.pool.reserve(estimate) if self.pool is not None and estimate else nullcontext()

    @contextmanager
    def aggregate_progress(self):
        """Expose only the composite operation's percentages to an active worker."""
        with jobs.suspend_progress() as listener:
            if listener is None:
                yield self
                return

            def emit(percentage):
                listener(percentage)
                if self.progress is not None:
                    self.progress(percentage)

            yield replace(self, progress=emit)

    def run(self, function, *, work_bytes=0):
        def observe(fraction):
            self._check()
            if self.progress is not None and fraction is not None and 0 < fraction < 1:
                self.progress(min(99, max(1, int(fraction * 100))))
            self._check()

        with self.reserve(work_bytes):
            with jobs.observe(observe):
                result = function()
            self.checkpoint()
        return result
