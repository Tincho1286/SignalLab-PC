"""A common definition of periodic waveforms in the two temporal domains."""

import sympy as sp


def period_value(period, *, discrete=False):
    if not isinstance(period, sp.Expr) or period.free_symbols or period.is_positive is not True or period.is_finite is not True:
        raise ValueError('El período debe ser una constante positiva y finita.')
    if discrete and period.is_integer is not True:
        raise ValueError('El período discreto debe ser un entero en muestras.')
    return period


def start_value(start, *, discrete=False):
    if not isinstance(start, sp.Expr) or start.free_symbols or start.is_real is not True or start.is_finite is not True:
        raise ValueError('El inicio del período debe ser una constante real finita.')
    if discrete and start.is_integer is not True:
        raise ValueError('El inicio discreto debe ser un índice entero.')
    return start


def width_value(width, period, *, discrete=False):
    if (not isinstance(width, sp.Expr) or width.free_symbols or width.is_nonnegative is not True
            or width.is_finite is not True or (period - width).is_nonnegative is not True):
        raise ValueError('El ancho del pulso debe estar entre cero y el período.')
    if discrete and width.is_integer is not True:
        raise ValueError('El ancho discreto debe ser un entero en muestras.')
    return width


class ImpulseTrain(sp.Function):
    """Continuous distribution with unit areas at multiples of the period."""

    nargs = 2


def repeat(value, variable, period, start=sp.S.Zero):
    if not isinstance(variable, sp.Symbol) or variable.name not in ('n', 't'):
        raise ValueError('Indicá n o t como segunda entrada de Repeat.')
    if not isinstance(value, sp.Expr) or any(symbol.name in ('n', 't', 'z', 's', 'w') and symbol != variable
                                            for symbol in value.free_symbols):
        raise ValueError('El tramo de Repeat debe usar la misma variable temporal que la señal.')
    if value.has(sp.DiracDelta, ImpulseTrain):
        raise ValueError('Para un tren de Dirac continuo, usá ImpulseTrain con su período y desplazamiento.')
    discrete = variable.name == 'n'
    period = period_value(period, discrete=discrete)
    start = start_value(start, discrete=discrete)
    return value.subs(variable, start + sp.Mod(variable - start, period))


def _discrete(argument):
    return any(symbol.name in ('n', 'k') for symbol in argument.free_symbols)


def pulse_train(argument, period, width):
    discrete = _discrete(argument)
    period = period_value(period, discrete=discrete)
    width = width_value(width, period, discrete=discrete)
    return sp.Piecewise((1, sp.Mod(argument, period) < width), (0, True))


def impulse_train(argument, period):
    discrete = _discrete(argument)
    period = period_value(period, discrete=discrete)
    if discrete:
        return sp.KroneckerDelta(sp.Mod(argument, period), 0)
    if not argument.free_symbols:
        raise ValueError('ImpulseTrain continuo requiere una variable temporal.')
    return ImpulseTrain(argument, period)


SYMBOLIC_FUNCTIONS = {'repeat': repeat, 'pulsetrain': pulse_train, 'impulsetrain': impulse_train}


def wrapped_period(value, variable):
    """Recover a complete half-open period from expressions using one phase."""
    phases = [phase for phase in value.atoms(sp.Mod) if phase.has(variable)]
    if len(phases) != 1:
        return None
    phase, = phases
    coordinate, period = phase.args
    origin = variable - coordinate
    if origin.free_symbols or origin.is_real is not True or not period.is_positive or not period.is_finite:
        return None
    if variable.is_integer and period.is_integer is not True:
        return None
    if value.xreplace({phase: sp.Dummy('phase')}).has(variable):
        return None
    first = sp.ceiling(origin) if variable.is_integer else origin
    return period, first, value.xreplace({phase: variable - origin})


def affine_train_term(term, variable):
    """Return the period, reference position and impulse area of one comb."""
    atoms = term.atoms(ImpulseTrain)
    if len(atoms) != 1:
        return None
    train, = atoms
    amplitude = term.extract_multiplicatively(train)
    if amplitude is None or amplitude.has(variable, ImpulseTrain):
        return None
    argument, period = train.args
    scale = sp.diff(argument, variable)
    shift = sp.simplify(argument - scale*variable)
    if scale.has(variable) or scale.is_real is not True or scale.is_zero is not False or shift.has(variable) or shift.is_real is not True:
        return None
    return period/sp.Abs(scale), -shift/scale, amplitude/sp.Abs(scale)


def sample_phase(coordinates, period):
    import numpy as np

    phase = np.remainder(coordinates, period)
    tolerance = 4 * np.spacing(np.abs(coordinates))
    tolerance = np.minimum(tolerance, period * 1e-8)
    return np.where(np.minimum(phase, period-phase) <= tolerance, 0, phase)
