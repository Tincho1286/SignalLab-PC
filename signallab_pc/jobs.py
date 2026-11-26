"""Cancelación cooperativa y progreso de cálculos por bloques."""
from contextlib import contextmanager
from threading import local

_context = local()


class OperationCancelled(Exception):
    pass


def bind(cancel_event, progress):
    _context.cancel_event = cancel_event
    _context.progress = progress


def clear():
    _context.__dict__.clear()


@contextmanager
def suspend_progress():
    """Let a composite operation emit progress without exposing nested fractions."""
    previous = getattr(_context, 'progress', None)
    _context.progress = None
    try:
        yield previous
    finally:
        _context.progress = previous


@contextmanager
def observe(callback):
    previous = getattr(_context, 'observer', None)
    def notify(fraction):
        if previous is not None:
            previous(fraction)
        callback(fraction)
    _context.observer = notify
    try:
        yield
    finally:
        _context.observer = previous


def checkpoint(fraction=None):
    event = getattr(_context, "cancel_event", None)
    if event is not None and event.is_set():
        raise OperationCancelled("Cálculo cancelado; no se guardó un resultado parcial.")
    observer = getattr(_context, 'observer', None)
    if observer is not None:
        observer(fraction)
    callback = getattr(_context, "progress", None)
    if fraction is not None and callback is not None:
        callback(max(0, min(100, int(fraction*100))))
