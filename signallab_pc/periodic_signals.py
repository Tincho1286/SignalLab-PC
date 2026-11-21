"""A common definition of periodic waveforms in the two temporal domains."""

import sympy as sp
import re


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


def repeat_samples(variable, start, samples, step=sp.S.One):
    """Periodize integer samples or their closed linear interpolation."""
    if not isinstance(variable, sp.Symbol) or variable.name not in ('n', 't'):
        raise ValueError('RepeatSamples requiere n o t como primera entrada.')
    discrete = variable.name == 'n'
    start = start_value(start, discrete=discrete)
    step = period_value(step, discrete=discrete)
    if discrete and step != 1:
        raise ValueError('Los índices de una secuencia tienen paso 1.')
    if not isinstance(samples, (tuple, sp.Tuple)) or not samples or any(
        not isinstance(sample, sp.Expr) or sample.free_symbols or sample.is_finite is not True for sample in samples
    ):
        raise ValueError('El período requiere una lista de muestras constantes finitas.')
    phase = sp.Mod(variable-start, step*len(samples))
    if discrete:
        return sp.Piecewise(*[(value, sp.Eq(phase,index))
                              for index,value in enumerate(samples[:-1])], (samples[-1], True))
    values = []
    for index, value in enumerate(samples):
        next_value = samples[(index+1) % len(samples)]
        segment = value+(next_value-value)*(phase/step-index)
        values.append((segment, phase<(index+1)*step if index<len(samples)-1 else True))
    return sp.Piecewise(*values)


SYMBOLIC_FUNCTIONS = {'repeat': repeat, 'pulsetrain': pulse_train, 'impulsetrain': impulse_train,
                      'repeatsamples': repeat_samples}


def _wrap_geometry(value, variable):
    phases = sorted((phase for phase in value.atoms(sp.Mod) if phase.has(variable)),key=sp.default_sort_key)
    if not phases or value.xreplace({phase:sp.Dummy('phase') for phase in phases}).has(variable):
        return None
    discrete=variable.is_integer is True
    entries=[]
    for phase in phases:
        coordinate,modulus=phase.args
        slope=sp.diff(coordinate,variable)
        offset=sp.simplify(coordinate-slope*variable)
        if (slope.free_symbols or offset.free_symbols or modulus.free_symbols or slope.is_real is not True
                or slope.is_zero is not False or offset.is_real is not True or modulus.is_positive is not True
                or any(part.is_finite is not True for part in (slope,offset,modulus))):
            return None
        rate=sp.simplify(slope/modulus)
        if discrete and rate.is_Rational is not True:return None
        entries.append((phase,coordinate,modulus,slope,offset,sp.Integer(rate.q) if discrete else modulus/sp.Abs(slope)))
    return entries


def _common_period(periods):
    from math import lcm

    base=periods[0]
    ratios=[sp.simplify(period/base) for period in periods]
    if any(ratio.is_Rational is not True for ratio in ratios):return None
    return sp.simplify(base*lcm(*(int(ratio.p) for ratio in ratios)))


def wrapped_period(value, variable):
    """Recover a full period for commensurate affine wrapped coordinates."""
    entries=_wrap_geometry(value,variable)
    if entries is None:return None
    discrete=variable.is_integer is True
    if len(entries)==1 and entries[0][3]==1:
        phase,coordinate,modulus,_,offset,period=entries[0]
        if not discrete or modulus==period:
            origin=-offset
            first=sp.ceiling(origin) if discrete else origin
            return period,first,value.xreplace({phase:coordinate})
    period=_common_period([entry[-1] for entry in entries])
    if period is None:return None
    if discrete:return period,sp.S.Zero,value
    from .jobs import checkpoint
    from .resources import ensure_working_set

    breaks={sp.S.Zero,period}
    for _,_,modulus,slope,offset,_ in entries:
        start,end=sorted((offset/modulus,(slope*period+offset)/modulus))
        first,last=sp.floor(start)+1,sp.ceiling(end)-1
        if not isinstance(first,sp.Integer) or not isinstance(last,sp.Integer):return None
        ensure_working_set(max(0,int(last-first+1))+len(breaks),bytes_per_sample=4096,live_arrays=8)
        for index in range(int(first),int(last+1)):
            checkpoint()
            breaks.add(sp.simplify((index*modulus-offset)/slope))
    points=sorted(breaks);pieces=[]
    for low,high in zip(points,points[1:]):
        checkpoint()
        midpoint=(low+high)/2
        substitutions={phase:coordinate-modulus*sp.floor(coordinate.subs(variable,midpoint)/modulus)
                       for phase,coordinate,modulus,_,_,_ in entries}
        pieces.append((value.xreplace(substitutions),variable<high if high!=period else True))
    return period,sp.S.Zero,sp.Piecewise(*pieces)


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


def has_explicit_period(source, domain):
    """Certify named periodic formulas without sampling or constructing a cycle."""
    if not re.search(r'\b(?:repeat|repeatsamples|pulsetrain|impulsetrain|mod)\s*\(|%',source,re.IGNORECASE):
        return False
    from .symbolic import N,T,parse

    variable=N if domain=='discrete' else T
    try:
        value=parse(source)
        regular=[]
        periods=[]
        for term in sp.Add.make_args(sp.expand_mul(value)):
            if term.has(ImpulseTrain):
                train=affine_train_term(term,variable)
                if train is None or train[0].is_finite is not True or train[2].is_finite is not True:return False
                periods.append(train[0])
            else:
                regular.append(term)
        ordinary=sp.Add(*regular)
        if ordinary.has(sp.DiracDelta) or ordinary.free_symbols-{variable}:return False
        if ordinary.has(variable):
            entries=_wrap_geometry(ordinary,variable)
            if entries is None:return False
            periods.extend(entry[-1] for entry in entries)
        return not periods or _common_period(periods) is not None
    except (SyntaxError,ValueError,TypeError,NotImplementedError):
        # Recognizing the infinite definition is optional for finite sampling.
        return False


def discrete_cycle(value, index):
    cycle = wrapped_period(value, index)
    if cycle is None:
        return None
    from .jobs import checkpoint
    from .resources import ensure_working_set

    period, origin, ordinary = cycle
    ensure_working_set(int(period), bytes_per_sample=1024, live_arrays=8)
    samples = []
    for position in range(int(origin), int(origin+period)):
        checkpoint()
        sample = sp.simplify(ordinary.subs(index, position))
        if sample.has(sp.zoo, sp.oo, -sp.oo, sp.nan):
            raise ValueError(f'El período incluye una muestra no finita en n = {position}.')
        samples.append(sample)
    return int(origin), samples


def cycle_weight(cycle, start, multiplier):
    origin, samples = cycle
    period = len(samples)
    start = int(start)
    ordered = ((start+k, samples[(start+k-origin) % period]) for k in range(period))
    return sp.Add(*(sample*multiplier(position) for position, sample in ordered if sample != 0))


def cycle_sum(cycle, lower, upper):
    """Sum an inclusive integer range, even if it covers many periods."""
    origin,samples=cycle
    count,remainder=divmod(int(upper-lower+1),len(samples))
    start=int(lower)-origin
    return count*sp.Add(*samples)+sp.Add(*(samples[(start+k) % len(samples)] for k in range(remainder)))


def cycle_dtft(cycle, frequency):
    origin, samples = cycle
    spacing = 2*sp.pi/len(samples)
    return spacing*cycle_weight(cycle, origin, lambda n: sp.exp(-sp.I*frequency*n))*ImpulseTrain(frequency, spacing)


def weighted_lines(term, variable, lower, upper, *, right_open=True):
    """Expand one weighted comb on a finite interval."""
    atoms = term.atoms(ImpulseTrain)
    if len(atoms) != 1:
        return None
    train, = atoms
    amplitude = term.extract_multiplicatively(train)
    if amplitude is None or amplitude.has(ImpulseTrain, sp.DiracDelta):
        raise ValueError('El espectro debe sumar las líneas. El producto de trenes de impulsos no está definido.')
    geometry = affine_train_term(train, variable)
    if geometry is None:
        return None
    from .jobs import checkpoint
    from .resources import ensure_working_set

    spacing, origin, area = geometry
    start = sp.ceiling((lower-origin)/spacing)
    edge = (upper-origin)/spacing
    stop = sp.ceiling(edge) if right_open else sp.floor(edge)+1
    if not isinstance(start, sp.Integer) or not isinstance(stop, sp.Integer):
        return None
    ensure_working_set(max(0, int(stop-start)), bytes_per_sample=1024, live_arrays=8)
    answer = []
    for index in range(int(start), int(stop)):
        checkpoint()
        phase = sp.simplify(origin+index*spacing)
        weight = sp.simplify(amplitude.subs(variable, phase))
        if weight.has(sp.nan, sp.zoo, sp.oo, -sp.oo) or amplitude.has(sp.Piecewise, sp.Heaviside, sp.sign):
            left = sp.limit(amplitude, variable, phase, dir='-')
            right = sp.limit(amplitude, variable, phase, dir='+')
            if left.is_finite is not True or sp.simplify(left-right)!=0:
                raise ValueError('El peso de una línea espectral es discontinuo o no finito en su frecuencia.')
            if weight.has(sp.nan, sp.zoo, sp.oo, -sp.oo):
                weight = left
            elif sp.simplify(left-weight)!=0:
                raise ValueError('El valor puntual de una línea difiere del límite de su peso.')
        if weight != 0:
            answer.append((phase, area*weight))
    return answer


def sample_phase(coordinates, period):
    import numpy as np

    phase = np.remainder(coordinates, period)
    tolerance = 4 * np.spacing(np.abs(coordinates))
    tolerance = np.minimum(tolerance, period * 1e-8)
    return np.where(np.minimum(phase, period-phase) <= tolerance, 0, phase)
