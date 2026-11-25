"""Estimación de memoria de trabajo basada en RAM disponible; no hereda topes HP."""
from __future__ import annotations

import ctypes
import os
from pathlib import Path, PurePosixPath
import sys


class ResourceLimitError(MemoryError):
    """El cálculo solicitado excede el presupuesto de memoria de trabajo actual."""


def _linux_memory_headroom(cgroup_file=Path('/proc/self/cgroup'), hierarchy=Path('/sys/fs/cgroup')):
    """Apply the tightest cgroup v2 memory cap that includes this process."""
    try:
        lines = cgroup_file.read_text(encoding='utf-8').splitlines()
    except OSError:
        return None
    scope = next((line[3:] for line in lines if line.startswith('0::')), None)
    if scope is None:
        return None
    components = PurePosixPath(scope)
    if not components.is_absolute() or '..' in components.parts:
        return None
    current = hierarchy.joinpath(*components.parts[1:])
    headroom = None
    while current == hierarchy or hierarchy in current.parents:
        try:
            limit = (current/'memory.max').read_text(encoding='ascii').strip()
            if limit != 'max':
                used = int((current/'memory.current').read_text(encoding='ascii'))
                free = max(0, int(limit) - used)
                headroom = free if headroom is None else min(headroom, free)
        except (OSError, ValueError):
            pass
        if current == hierarchy:
            break
        current = current.parent
    return headroom


def available_physical_memory() -> int:
    """Devuelve RAM física disponible en Windows o sistemas con sysconf."""
    if sys.platform == "win32":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError("Windows no pudo informar la memoria física disponible.")
        return int(status.ullAvailPhys)
    try:
        physical = int(os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    except (ValueError, OSError, AttributeError):
        raise OSError("No se pudo estimar la memoria física disponible en este sistema.")
    if sys.platform == 'linux':
        limited = _linux_memory_headroom()
        if limited is not None:
            return min(physical, limited)
    return physical


def ensure_working_set(sample_count: int, *, bytes_per_sample: int = 16,
                       live_arrays: int = 4, fraction_of_available: float = 0.35,
                       available_bytes: int | None = None) -> int:
    """Comprueba una estimación dependiente de RAM libre, no un máximo fijo de muestras."""
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 0:
        raise ValueError("La cantidad de muestras debe ser un entero no negativo.")
    if bytes_per_sample < 1 or live_arrays < 1:
        raise ValueError("La estimación de memoria debe ser positiva.")
    if not 0 < fraction_of_available <= 0.8:
        raise ValueError("La reserva debe estar entre 0 y 80 % de la RAM disponible.")
    if sample_count > sys.maxsize // (bytes_per_sample * live_arrays):
        raise ResourceLimitError("La dimensión excede el espacio de direcciones de este Python.")
    available = available_physical_memory() if available_bytes is None else int(available_bytes)
    required = sample_count * bytes_per_sample * live_arrays
    budget = int(available * fraction_of_available)
    if required > budget:
        mib = required / (1024 ** 2)
        free_mib = available / (1024 ** 2)
        raise ResourceLimitError(
            f"El cálculo estima {mib:,.0f} MiB de memoria temporal; "
            f"hay {free_mib:,.0f} MiB disponibles. Reducí el tamaño o liberá memoria."
        )
    return required
