"""Estimación de memoria de trabajo basada en RAM disponible; no hereda topes HP."""
from __future__ import annotations

import ctypes
import os
import sys


class ResourceLimitError(MemoryError):
    """El cálculo solicitado excede el presupuesto de memoria de trabajo actual."""


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
        return int(os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    except (ValueError, OSError, AttributeError):
        raise OSError("No se pudo estimar la memoria física disponible en este sistema.")


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
