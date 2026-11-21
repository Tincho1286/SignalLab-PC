"""Distributional Fourier transforms of periodic half-axis signals."""

import sympy as sp

from .jobs import checkpoint
from .periodic_signals import ImpulseTrain, PVCot, cycle_weight, discrete_cycle


SCOPE = ('La cola periódica se calcula como límite de Abel. El resultado combina líneas espectrales y un valor '
         'principal de Cauchy, indicado por PVCot(w,P) = VP de cot(P·w/2). La serie o integral ordinaria diverge.')


def cotangent_geometry(value,frequency):
    argument,period=value.args
    slope=sp.diff(argument,frequency)
    intercept=sp.simplify(argument-slope*frequency)
    if (period.free_symbols or period.is_positive is not True or period.is_finite is not True
            or slope.free_symbols or slope.is_real is not True or slope.is_zero is not False
            or intercept.free_symbols or intercept.is_real is not True or intercept.is_finite is not True):
        return None
    return sp.simplify(period*sp.Abs(slope)),sp.simplify(-intercept/slope),sp.sign(slope)


def principal_projection(value,frequency,lower,upper):
    """Evaluate the ordinary part away from net principal-value poles."""
    from .resources import ensure_working_set
    terms=[]
    residues={}
    for term in sp.Add.make_args(sp.expand_mul(value)):
        atoms=term.atoms(PVCot)
        if not atoms:
            terms.append(term)
            continue
        if len(atoms)!=1:raise ValueError('Separá los valores principales en términos aditivos.')
        principal,=atoms
        weight=term.extract_multiplicatively(principal)
        geometry=cotangent_geometry(principal,frequency)
        if weight is None or weight.has(PVCot) or geometry is None:
            raise ValueError('El gráfico requiere valores principales lineales con período y desplazamiento reales.')
        period,origin,orientation=geometry
        spacing=2*sp.pi/period
        first=sp.ceiling((lower-origin)/spacing)
        last=sp.floor((upper-origin)/spacing)
        if not isinstance(first,sp.Integer) or not isinstance(last,sp.Integer):
            raise ValueError('No se pudieron ubicar los polos del valor principal.')
        ensure_working_set(max(0,int(last-first+1))+len(residues),bytes_per_sample=1024,live_arrays=8)
        for harmonic in range(int(first),int(last+1)):
            checkpoint()
            position=sp.simplify(origin+spacing*harmonic)
            at=sp.simplify(weight.subs(frequency,position))
            if at.is_finite is not True:
                raise ValueError('El peso de un valor principal debe ser finito en cada polo.')
            residues[position]=residues.get(position,sp.S.Zero)+2*orientation*at/period
        terms.append(weight*orientation*sp.cot(period*(frequency-origin)/2))
    poles=sorted(position for position,residue in residues.items() if sp.simplify(residue).is_zero is not True)
    return sp.Add(*terms),poles


def _half_comb(weight, period, direction, frequency):
    """Abel limit of the geometric series of repeated cycles."""
    return (weight*(1-direction*sp.I*PVCot(frequency,period))/2
            + sp.pi/period*weight*ImpulseTrain(frequency,2*sp.pi/period))


def discrete_spectrum(value, index, frequency, z, lower, upper):
    if not value.has(sp.Mod) or lower.is_finite and upper.is_finite:
        return None
    from .z_direct_pairs import interval,pieces

    parts=pieces(value,lower,upper)
    if parts is None:return None
    terms=[]
    has_tail=False
    for branch,start,stop in parts:
        checkpoint()
        if branch==0:continue
        if start.is_finite and stop.is_finite:
            finite=interval(branch,start,stop)
            if finite is None:return None
            terms.append(finite[0].subs(z,sp.exp(sp.I*frequency)))
            continue
        if start==-sp.oo and stop==sp.oo:return None
        cycle=discrete_cycle(branch,index)
        if cycle is None and not branch.has(index):cycle=(0,[branch])
        if cycle is None:return None
        period=len(cycle[1])
        direction=1 if start.is_finite else -1
        origin=start if direction==1 else stop-period+1
        weight=cycle_weight(cycle,origin,lambda position:sp.exp(-sp.I*frequency*position))
        if weight==0:continue
        terms.append(_half_comb(weight,sp.Integer(period),direction,frequency))
        has_tail=True
    return sp.Add(*terms) if has_tail else None


def continuous_spectrum(value,time,frequency):
    if value.has(ImpulseTrain, sp.DiracDelta, PVCot):
        if value.has(sp.DiracDelta,PVCot):return None
        from .gated_impulse_trains import partition_trains,spectrum

        spans, remainder=partition_trains(value,time)
        if remainder!=0:return None
        terms = [spectrum(span, frequency) for span in spans]
        return None if None in terms else sp.Add(*terms)
    from .periodic_fourier import _bounded_cycle,finite_laplace_piece,imaginary_axis,periodic_integral
    from .periodic_signals import continuous_periodic_components
    from .periodic_support import split_periodic_support

    parts=split_periodic_support(value,time,preserve_addends=True)
    if parts is None:return None
    parameter=sp.Dummy('laplace_frequency')

    def integrate(branch,lower,upper):
        result=(periodic_integral(branch,time,lower,upper,laplace_variable=parameter) if branch.has(sp.Mod)
                else finite_laplace_piece(branch,time,parameter,lower,upper))
        if result is None or result.has(sp.Integral,sp.nan,sp.zoo,sp.oo):return None
        return sp.factor_terms(imaginary_axis(result,parameter,frequency))

    terms=[]
    has_tail=False
    for branch,start,stop in parts:
        checkpoint()
        if branch==0:continue
        if start.is_finite and stop.is_finite:
            weight=integrate(branch,start,stop)
            if weight is None:return None
            terms.append(weight)
            continue
        if start==-sp.oo and stop==sp.oo:return None
        cycle=_bounded_cycle(branch,time)
        if cycle is not None or not branch.has(time):
            components=[(cycle[0] if cycle is not None else None,branch)]
        else:
            components=continuous_periodic_components(branch,time)
            if components is None:return None
            if any(waveform.has(sp.Mod) and _bounded_cycle(waveform,time) is None for _,waveform in components):
                return None
        direction=1 if start.is_finite else -1
        for period,waveform in components:
            period=period if period is not None else sp.S.One
            left,right=(start,start+period) if direction==1 else (stop-period,stop)
            weight=integrate(waveform,left,right)
            if weight is None:return None
            if weight==0:continue
            terms.append(_half_comb(weight,period,direction,frequency))
            has_tail=True
    return sp.Add(*terms) if has_tail else None
