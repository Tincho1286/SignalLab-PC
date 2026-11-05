"""Closed Fourier inverse for ideal piecewise-constant frequency bands."""
import sympy as sp


def _split_mods(value, frequency, domain, terms):
    """Unwrap affine periodic coordinates over one canonical period."""
    bounds={domain.start,domain.end}
    wraps={}
    for term in terms:
        argument,period=term.args
        if not period.is_positive or not period.is_finite or period.free_symbols:
            return None
        argument=sp.expand(argument)
        slope=argument.coeff(frequency)
        offset=argument-slope*frequency
        if (offset.free_symbols or slope.free_symbols or slope.is_real is not True
                or slope.is_zero is not False or offset.is_real is not True):
            return None
        left=(slope*domain.start+offset)/period
        right=(slope*domain.end+offset)/period
        first=sp.floor(sp.Min(left,right))+1
        last=sp.ceiling(sp.Max(left,right))-1
        if not isinstance(first,sp.Integer) or not isinstance(last,sp.Integer) or last-first>128:
            return None
        bounds.update(sp.simplify((turn*period-offset)/slope) for turn in range(int(first),int(last)+1))
        if len(bounds)>129:return None
        wraps[term]=(argument,period)
    bounds=sorted(bounds,key=lambda point:float(point.evalf(25)))
    segments=[]
    for lower,upper in zip(bounds,bounds[1:]):
        if (lower<upper) is not sp.true:return None
        middle=(lower+upper)/2
        replacements={}
        for term,(argument,period) in wraps.items():
            turns=sp.floor(argument.subs(frequency,middle)/period)
            if not isinstance(turns,sp.Integer):return None
            replacements[term]=argument-period*turns
        segments.append((value.xreplace(replacements),sp.Interval(lower,upper)))
    return segments


def _folded_segments(value, frequency, domain):
    from .jobs import checkpoint
    pending=[(value,domain)]
    segments=[]
    while pending:
        checkpoint()
        expression,interval=pending.pop()
        wraps=expression.atoms(sp.Mod)
        if not wraps:
            segments.append((expression,interval))
            continue
        terms=[term for term in wraps if not term.has(*[other for other in wraps if other!=term])]
        split=_split_mods(expression,frequency,interval,terms)
        if split is None or len(segments)+len(pending)+len(split)>128:return None
        pending.extend(split)
    return segments


def _gain_and_delay(amplitude,frequency):
    """Separate the constant gains and delays of a sum of linear phases."""
    terms=[]
    for term in sp.Add.make_args(sp.expand_mul(amplitude)):
        if not term.has(frequency):
            terms.append((term,sp.S.Zero));continue
        gain,phase=sp.powsimp(term,combine='exp').as_independent(frequency,as_Add=False)
        if phase.func is not sp.exp:return None
        exponent=sp.expand(phase.args[0]);slope=exponent.coeff(frequency)
        remainder=exponent-slope*frequency;delay=sp.simplify(sp.I*slope)
        if remainder.has(frequency) or delay.has(frequency) or delay.is_real is not True:return None
        terms.append((gain*sp.exp(remainder),delay))
    return terms


def _band_intervals(value,frequency,domain):
    from sympy.core.relational import Relational
    from .jobs import checkpoint
    segments=_folded_segments(value,frequency,domain) if domain!=sp.S.Reals else [(value,domain)]
    if segments is None:return None
    intervals=[]
    for value,segment in segments:
        checkpoint()
        piece=sp.piecewise_fold(value.rewrite(sp.Piecewise) if value.has(sp.Heaviside) else value)
        if isinstance(piece,sp.Piecewise):
            for amplitude,condition in piece.args:
                for relation in condition.atoms(Relational):
                    edge=relation.lhs-relation.rhs
                    edge=edge.xreplace({absolute:absolute.args[0] for absolute in edge.atoms(sp.Abs)})
                    if edge.free_symbols-{frequency} or not edge.is_polynomial(frequency) or sp.degree(edge,frequency)>1:return None
            try:pairs=piece.as_expr_set_pairs(domain=segment)
            except (NotImplementedError,TypeError,ValueError):return None
        else:pairs=[(piece,segment)]
        for amplitude,region in pairs:
            for part in region.args if isinstance(region,sp.Union) else (region,):
                if isinstance(part,sp.FiniteSet) or part is sp.S.EmptySet:continue
                if not isinstance(part,sp.Interval) or amplitude.has(sp.nan,sp.zoo,sp.oo,-sp.oo):return None
                intervals.append((amplitude,part.start,part.end))
                if len(intervals)>128:return None
    coverage=sp.Union(*(sp.Interval(a,b) for _,a,b in intervals))
    return intervals if coverage==domain else None


def inverse_bands(value, frequency, time, *, discrete, period_origin=-sp.pi):
    domain=sp.Interval(period_origin,period_origin+2*sp.pi) if discrete else sp.S.Reals
    intervals=_band_intervals(value,frequency,domain)
    if not intervals:return None
    baseline=sp.S.Zero
    impulses=sp.S.Zero
    if not discrete:
        left=next((amplitude for amplitude,a,_ in intervals if a==-sp.oo),None)
        right=next((amplitude for amplitude,_,b in intervals if b==sp.oo),None)
        if left is None or right is None or sp.simplify(left-right)!=0:return None
        bands=_gain_and_delay(left,frequency)
        if bands is None:return None
        baseline=left
        impulses=sp.Add(*(gain*sp.DiracDelta(time-delay) for gain,delay in bands))
    from .jobs import checkpoint
    groups={}
    for amplitude,lower,upper in intervals:
        checkpoint()
        amplitude=sp.simplify(amplitude-baseline)
        if amplitude==0:continue
        if lower==-sp.oo or upper==sp.oo:return None
        bands=_gain_and_delay(amplitude,frequency)
        if bands is None:return None
        for gain,delay in bands:
            shifted=time-delay
            width=upper-lower;center=(lower+upper)/2
            origin,terms=groups.setdefault(delay,([],[]))
            origin.append(gain*width/(2*sp.pi))
            terms.append(gain*sp.exp(sp.I*center*shifted)*sp.sin(width*shifted/2))
    inverse=[]
    for delay,(origin,terms) in groups.items():
        shifted=time-delay
        numerator=sp.Add(*terms)
        at_origin=sp.simplify(sp.Add(*origin))
        if numerator==0 and discrete:
            inverse.append(at_origin*sp.KroneckerDelta(time,delay))
        else:
            inverse.append(sp.Piecewise((at_origin,sp.Eq(time,delay)),(numerator/(sp.pi*shifted),True)))
    return sp.Add(*inverse)+impulses


def frequency_definition(request):
    """Keep the formula separate from samples; use only fast, certified pairs."""
    from .symbolic import parse,W,N,T,S,Z
    from .expression_dialects import to_symbolic
    from .signal_notation import source
    from .cas_engine import encode
    text=to_symbolic(request['expression'])
    value=parse(text)
    if value.has(N,T,S,Z):raise ValueError('La definición de frecuencia usa w.')
    discrete=request.get('domain')=='discrete'
    output=N if discrete else T
    origin=parse(request['period_origin']) if discrete and request.get('period_origin') is not None else -sp.pi
    if origin.is_real is not True or origin.is_finite is not True or origin.free_symbols:
        raise ValueError('El origen del período de frecuencia debe ser real, finito y numérico.')
    known_period=not discrete or 'period_origin' in request or request.get('canonical_period',True)
    try:
        exact=inverse_bands(value,W,output,discrete=discrete,period_origin=origin) if known_period else None
    except (NotImplementedError, ValueError, TypeError, ArithmeticError):
        exact=None
    inverse=None
    already_periodic=not value.has(W)
    if exact is not None:
        inverse={'result':source(exact),'output_variable':str(output),'evaluated':True,'cas_encoded':encode(exact),
                 'scope':'Inversa de la definición algebraica completa. Los valores aislados de la frecuencia tienen medida nula.'}
    elif discrete and known_period and not value.has(sp.Piecewise) and sp.count_ops(value)<48:
        from .inverse_dtft_algebra import rational_z
        equivalent=rational_z(value)
        already_periodic=equivalent is not None
        if equivalent is not None and not equivalent.free_symbols-{Z}:
            num,den=sp.fraction(equivalent)
            if max(sp.degree(num,Z),sp.degree(den,Z))<=6:
                from .z_inverse import inverse as inverse_z
                try:
                    result=inverse_z({'expression':str(equivalent),'roc':'radius','radius':'1','include_samples':False})
                except ValueError:result=None
                if result and result.get('evaluated',True):
                    inverse={**result,'output_variable':'n','evaluated':True}
    scope='Definición algebraica en frecuencia, separada de su rejilla numérica.'
    if discrete and known_period:
        if not already_periodic and sp.count_ops(value)<48:
            from sympy.calculus.util import periodicity
            try:
                fundamental=periodicity(value,W)
                already_periodic=fundamental==0 or fundamental is not None and (2*sp.pi/fundamental).is_integer is True
            except (NotImplementedError,TypeError,ValueError,ArithmeticError):pass
        if not already_periodic:
            value=value.xreplace({W:sp.Mod(W-origin,2*sp.pi)+origin})
            text=source(value)
        scope+=' En discreto se extiende cada 2π la definición desde el origen '+str(origin)+' rad/muestra.'
    return {'definition':{'result':text,'output_variable':'w','frequency_units':'rad/muestra' if discrete else 'rad/s',
                          'evaluated':True,'cas_encoded':encode(value),'scope':scope},
            'inverse':inverse}
