"""Recover expected failures only at explicit optional-result boundaries."""
from .resources import ResourceLimitError


def optional(label, compute):
    from .jobs import OperationCancelled
    try:
        return compute(), None
    except OperationCancelled:
        raise
    except (ValueError, ArithmeticError, RuntimeError, ResourceLimitError) as exc:
        return None, label+': '+str(exc)+' El resultado principal se conserva.'
    except Exception as exc:
        import traceback
        from .runtime_diagnostics import diagnostic
        diagnostic(exc,details=traceback.format_exc(),context=label)
        return None,label+': falló esta etapa complementaria. El resultado principal se conserva; el diagnóstico quedó registrado localmente.'


def presentation(label, compute, fallback):
    """A formatting bug must not erase an already computed mathematical object."""
    from .jobs import OperationCancelled
    try:
        return compute(), None
    except OperationCancelled:
        raise
    except Exception as exc:
        import traceback
        from .runtime_diagnostics import diagnostic
        diagnostic(exc, details=traceback.format_exc(), context=label)
        return fallback(), label+' no disponible. Se conserva el resultado calculado y se usa una vista sencilla.'
