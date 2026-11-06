"""Exact direct-Z pairs on disjoint integer supports, before generic summation."""
import sympy as sp
from .symbolic import N,Z
from .jobs import checkpoint


def intervals(region):
    if region is sp.S.EmptySet:return []
    if region==sp.S.Reals:region=sp.Interval(-sp.oo,sp.oo)
    if isinstance(region,sp.Union):
        items=[intervals(part) for part in region.args]
        return None if any(item is None for item in items) else [pair for item in items for pair in item]
    if isinstance(region,sp.FiniteSet):
        if any(value.is_integer is None for value in region):return None
        return [(value,value) for value in region if value.is_integer]
    if not isinstance(region,sp.Interval):return None
    lo=region.start if region.start==-sp.oo else sp.ceiling(region.start)
    hi=region.end if region.end==sp.oo else sp.floor(region.end)
    if region.left_open and lo==region.start:lo+=1
    if region.right_open and hi==region.end:hi-=1
    if not (lo==-sp.oo or isinstance(lo,sp.Integer)) or not (hi==sp.oo or isinstance(hi,sp.Integer)):return None
    return [(lo,hi)] if lo<=hi else []


def pieces(expression,lower,upper,*,preserve_structure=False):
    # Keep the explicitly completed sample separate before integer identities
    # such as sin(pi*n)=0 simplify the regular branch.
    value=expression.replace(lambda v:v.func in (sp.Heaviside,sp.KroneckerDelta),lambda v:v.rewrite(sp.Piecewise))
    # Resolve real absolute values and signs into their actual supports before
    # looking for geometric tails. An even exponential has two different ratios.
    value=sp.piecewise_fold(value.rewrite(sp.Piecewise))
    def branch(value):return value if preserve_structure else sp.simplify(value)
    if not isinstance(value,sp.Piecewise):return [(branch(value),lower,upper)]
    try:parts=value.as_expr_set_pairs()
    except (NotImplementedError,ValueError,TypeError):return None
    result=[];support=sp.Interval(lower,upper)
    missing=intervals(support-sp.Union(*[region for _,region in parts]))
    if missing is None or missing:return None
    for amplitude,region in parts:
        bounds=intervals(region.intersect(support))
        if bounds is None:return None
        result.extend((branch(amplitude),lo,hi) for lo,hi in bounds)
    return result


def tail(r,power,start):
    """Sum k^power*r^k from a positive integer start to infinity."""
    if power>=0:
        from .resources import ensure_working_set
        ensure_working_set(power+1,bytes_per_sample=8192,live_arrays=8)
        q=sp.Dummy('q');value=q**start/(1-q)
        for _ in range(power):checkpoint();value=sp.cancel(q*sp.diff(value,q))
        return value.subs(q,r)
    if start>24:return r**start*sp.lerchphi(r,-power,start)
    base=-sp.log(1-r) if power==-1 else sp.polylog(-power,r)
    return base-sp.Add(*[r**k/sp.Integer(k)**(-power) for k in range(1,int(start))])


def half(term,start):
    """Recognize shifted polynomial/exponential pairs and reciprocal powers."""
    # Rewriting powers as exponentials and distributing products can collect a
    # common exponential into an additive denominator. Restore the separable
    # factors before inspecting the affine power; grouping is not semantics.
    term=sp.factor_terms(sp.powsimp(term));shift=sp.S.Zero;power=0
    for factor in sp.Mul.make_args(term):
        base,exponent=factor.as_base_exp()
        if not isinstance(exponent,sp.Integer):continue
        try:polynomial=sp.Poly(base,N)
        except sp.PolynomialError:continue
        if polynomial.degree()==1:
            root=sp.cancel(-polynomial.nth(0)/polynomial.nth(1))
            if root.is_real is True and root.is_finite is True:shift=root;power=int(exponent);break
    k=sp.Dummy('k',integer=True)
    shifted=term.subs(N,k+shift)
    regular=sp.powsimp(sp.cancel(shifted/k**power))
    ratio=sp.simplify(regular.subs(k,k+1)/regular)
    coefficient=sp.simplify(regular.subs(k,0))
    if ratio.has(k,sp.nan,sp.zoo,sp.oo) or coefficient.has(k,sp.nan,sp.zoo,sp.oo):return None
    # A k-independent exact successive-term ratio certifies a geometric pair.
    # Expand numeric phases to Cartesian constants rather than principal
    # fractional powers of -1, which obscure real sinusoidal pairs.
    constant,dependent=ratio.as_independent(Z,as_Add=False)
    if constant.is_number:ratio=sp.expand_complex(constant)*dependent
    interior=sp.Abs(ratio)<1
    # Ordinary boundary convergence is certified separately from an open Z
    # annulus. Dirichlet applies to reciprocal powers off resonance; powers
    # below -1 converge absolutely even at resonance. A step is excluded.
    boundary=sp.Or(interior,sp.And(sp.Eq(sp.Abs(ratio),1),sp.Ne(ratio,1) if power==-1 else sp.true)) if power<0 else interior
    lo=start-shift
    if not isinstance(shift,sp.Integer):
        # A noninteger centre is not a missing integer sample. Sum from the
        # actual integer support edge with the Hurwitz/Lerch geometric pair.
        if power<0:
            amplitude=sp.simplify(regular.subs(k,lo))
            return amplitude*sp.lerchphi(ratio,-power,lo),interior,boundary
        return None
    if power<0 and lo<=0:return None
    if lo<=0:
        prefix=sp.summation(shifted,(k,lo,0));lo=sp.S.One
        if prefix.has(sp.Sum,sp.nan,sp.zoo,sp.oo):return None
    else:prefix=sp.S.Zero
    return sp.simplify(prefix+coefficient*tail(ratio,power,lo)),interior,boundary


def interval(value,lower,upper):
    if value==0:return sp.S.Zero,sp.true,sp.true
    if lower==upper:return sp.simplify(value.subs(N,lower)*Z**(-lower)),sp.true,sp.true
    if lower.is_finite and upper.is_finite:
        result=sp.summation(value*Z**(-N),(N,lower,upper))
        return None if result.has(sp.Sum,sp.nan,sp.zoo,sp.oo) else (result,sp.true,sp.true)
    if lower==-sp.oo and upper==sp.oo:
        left=interval(value,-sp.oo,sp.S.NegativeOne);right=interval(value,sp.S.Zero,sp.oo)
        return None if left is None or right is None else (left[0]+right[0],sp.And(left[1],right[1]),sp.And(left[2],right[2]))
    term=value*Z**(-N)
    if lower==-sp.oo:term=term.subs(N,-N);lower=-upper
    expanded=sp.expand_mul(term.rewrite(sp.exp));results=[]
    for item in sp.Add.make_args(expanded):
        checkpoint()
        if item==0:continue
        pair=half(item,lower)
        if pair is None:return None
        results.append(pair)
    return sp.Add(*[p[0] for p in results]),sp.And(*[p[1] for p in results]),sp.And(*[p[2] for p in results])


def direct_pairs(expression,lower,upper):
    parts=pieces(expression,lower,upper)
    if parts is None:return None
    results=[];segments=[]
    for value,lo,hi in parts:
        checkpoint();pair=interval(value,lo,hi)
        if pair is None:return None
        results.append(pair)
        segments.append(dict(expression=str(value),lower=str(lo),upper=str(hi),transform=str(pair[0]),condition=str(pair[1])))
    from .radial_conditions import simplify_radial
    condition = simplify_radial(sp.And(*(pair[1] for pair in results)), Z)
    boundary_condition=sp.And(*[pair[2] for pair in results])
    closed=sp.simplify(sp.Add(*[pair[0] for pair in results]))
    boundary={'segments':segments,'boundary_result':closed,'boundary_condition':boundary_condition}
    if condition is sp.false:
        return {'result':sp.Sum(expression*Z**(-N),(N,lower,upper)),'condition':condition,'empty':True,**boundary}
    finite_support=all(value==0 or (lo.is_finite and hi.is_finite) for value,lo,hi in parts)
    return {'result':closed,'condition':condition,'empty':False,'finite_support':bool(finite_support),**boundary}
