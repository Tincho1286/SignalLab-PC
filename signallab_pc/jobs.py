"""Cancelación cooperativa y progreso de cálculos por bloques."""
from threading import local

_context = local()


class OperationCancelled(Exception):
    pass


def bind(cancel_event, progress):
    _context.cancel_event = cancel_event
    _context.progress = progress


def clear():
    _context.__dict__.clear()


def checkpoint(fraction=None):
    event = getattr(_context, "cancel_event", None)
    if event is not None and event.is_set():
        raise OperationCancelled("Cálculo cancelado; no se guardó un resultado parcial.")
    callback = getattr(_context, "progress", None)
    if fraction is not None and callback is not None:
        callback(max(0, min(100, int(fraction*100))))
