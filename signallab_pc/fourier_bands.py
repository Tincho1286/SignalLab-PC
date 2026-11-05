"""Closed Fourier inverse for ideal piecewise-constant frequency bands."""
import sympy as sp


def inverse_bands(value, frequency, time, *, discrete):
    domain=sp.Interval(-sp.pi,sp.pi) if discrete else sp.S.Reals
    if discrete:
        # This wrapping is the representation emitted by the direct DTFT.
        # On the integration interval it equals its argument almost everywhere.
        wrapped={term:frequency+sp.pi for term in value.atoms(sp.Mod)
                 if sp.expand(term.args[0]-frequency-sp.pi)==0 and sp.expand(term.args[1]-2*sp.pi)==0}
        value=value.xreplace(wrapped)
    piece=sp.piecewise_fold(value.rewrite(sp.Piecewise) if value.has(sp.Heaviside) else value)
    if not isinstance(piece,sp.Piecewise):
        if piece.has(frequency) or piece.has(sp.nan,sp.zoo,sp.oo,-sp.oo):return None
        return piece*(sp.KroneckerDelta(time,0) if discrete else sp.DiracDelta(time))
    def gain_and_delay(amplitude):
        # A linear phase in a band represents a time shift of its inverse.
        if not amplitude.has(frequency):return amplitude,sp.S.Zero
        amplitude=sp.powsimp(amplitude,combine='exp')
        gain,phase=amplitude.as_independent(frequency,as_Add=False)
        if phase==1:return gain,sp.S.Zero
        if phase.func is not sp.exp:return None
        exponent=sp.expand(phase.args[0]);slope=exponent.coeff(frequency)
        remainder=exponent-slope*frequency;delay=sp.simplify(sp.I*slope)
        if remainder.has(frequency) or delay.has(frequency) or delay.is_real is not True:return None
        return gain*sp.exp(remainder),delay

    # Linear frequency comparisons certify the intervals of each band.
    from sympy.core.relational import Relational
    for amplitude,condition in piece.args:
        if gain_and_delay(amplitude) is None:return None
        for relation in condition.atoms(Relational):
            edge=(relation.lhs-relation.rhs).xreplace({sp.Abs(frequency):frequency})
            if edge.free_symbols-{frequency} or not edge.is_polynomial(frequency) or sp.degree(edge,frequency)>1:return None
    try:pairs=piece.as_expr_set_pairs(domain=domain)
    except (NotImplementedError,TypeError,ValueError):return None
    intervals=[]
    for amplitude,region in pairs:
        for segment in region.args if isinstance(region,sp.Union) else (region,):
            if isinstance(segment,sp.FiniteSet) or segment is sp.S.EmptySet:continue
            if not isinstance(segment,sp.Interval) or amplitude.has(sp.nan,sp.zoo,sp.oo,-sp.oo):
                return None
            intervals.append((amplitude,segment.start,segment.end))
            if len(intervals)>128:return None
    if not intervals:return None
    coverage=sp.Union(*(sp.Interval(a,b) for _,a,b in intervals))
    if coverage!=domain:return None
    baseline=sp.S.Zero
    if not discrete:
        left=next((amplitude for amplitude,a,_ in intervals if a==-sp.oo),None)
        right=next((amplitude for amplitude,_,b in intervals if b==sp.oo),None)
        if left is None or right is None or left.has(frequency) or sp.simplify(left-right)!=0:return None
        baseline=left
    from .jobs import checkpoint
    groups={}
    for amplitude,lower,upper in intervals:
        checkpoint()
        amplitude=sp.simplify(amplitude-baseline)
        if amplitude==0:continue
        if lower==-sp.oo or upper==sp.oo:return None
        band=gain_and_delay(amplitude)
        if band is None:return None
        gain,delay=band
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
    regular=sp.Add(*inverse)
    return regular if discrete else regular+baseline*sp.DiracDelta(time)


def frequency_definition(request):
    """Keep the formula separate from samples; use only fast, certified pairs."""
    from .symbolic import parse,W,N,T,S,Z
    from .expression_dialects import to_symbolic
    from .signal_notation import source
    text=to_symbolic(request['expression'])
    value=parse(text)
    if value.has(N,T,S,Z):raise ValueError('La definición de frecuencia usa w.')
    discrete=request.get('domain')=='discrete'
    output=N if discrete else T
    exact=inverse_bands(value,W,output,discrete=discrete) if not discrete or request.get('canonical_period',True) else None
    inverse=None
    if exact is not None:
        inverse={'result':source(exact),'output_variable':str(output),'evaluated':True,
                 'scope':'Inversa de la definición algebraica completa. Los valores aislados de la frecuencia tienen medida nula.'}
    elif discrete and request.get('canonical_period',True) and not value.has(sp.Piecewise) and sp.count_ops(value)<48:
        from .inverse_dtft_algebra import rational_z
        equivalent=rational_z(value)
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
    if discrete and request.get('canonical_period',True) and exact is not None and value.has(sp.Piecewise,sp.Heaviside):
        if not value.has(sp.Mod):
            text=source(value.xreplace({W:sp.Mod(W+sp.pi,2*sp.pi)-sp.pi}))
        scope+=' En discreto, la banda entre −π y π se repite cada 2π.'
    return {'definition':{'result':text,'output_variable':'w','frequency_units':'rad/muestra' if discrete else 'rad/s',
                          'evaluated':True,'scope':scope},
            'inverse':inverse}
