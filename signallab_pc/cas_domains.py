"""Validity conditions for algebraic operations in a CAS worksheet."""
import sympy as sp


def bare(value):
    # Conditions must remain meaningful after a worksheet assumption changes.
    return value.xreplace({s:sp.Symbol(s.name) for s in value.free_symbols})


def substitute(value, pairs):
    if isinstance(value, list):
        return [substitute(item, pairs) for item in value]
    if isinstance(value, tuple):
        return tuple(substitute(item, pairs) for item in value)
    if isinstance(value, dict):
        result={substitute(key,pairs):substitute(item,pairs) for key,item in value.items()}
        if len(result)!=len(value):
            raise ValueError('La sustitución hace coincidir claves distintas.')
        return result
    if not pairs or not hasattr(value,'subs'):return value
    if isinstance(value,sp.MatrixBase):return value.applyfunc(lambda entry:substitute(entry,pairs))
    introduced={symbol for _,replacement in pairs for symbol in replacement.free_symbols}
    if introduced and any(introduced.intersection(getattr(node,'bound_symbols',())) for node in sp.preorder_traversal(value)):
        value=value.as_dummy()
        canonical={s for s in value.atoms(sp.Symbol) if s.name.startswith('_') and s.name[1:].isdigit()}
        value=value.xreplace({s:sp.Dummy('bound') for s in canonical})
    return value.subs(pairs, simultaneous=True)


def function_domain(command, args):
    if not args or not isinstance(args[0],sp.Expr):return sp.true
    value=bare(args[0])
    if command=='tan':return sp.Ne(sp.cos(value),0)
    if command=='tanh':return sp.Ne(sp.cosh(value),0)
    if command in {'log','ln'}:
        if len(args)==2 and isinstance(args[1],sp.Expr):
            base=bare(args[1]);return sp.And(sp.Ne(value,0),sp.Ne(base,0),sp.Ne(base,1))
        return sp.Ne(value,0)
    if command=='atan':return sp.Ne(value**2+1,0)
    if command=='atanh':return sp.Ne(value**2-1,0)
    if command in {'gamma','factorial'}:
        pole=sp.And(sp.Eq(sp.im(value),0),sp.Eq(sp.re(value),sp.floor(sp.re(value))),
                    sp.re(value)<=(0 if command=='gamma' else -1))
        return sp.Not(pole)
    return sp.true


def with_domain(result, variables, condition):
    if condition is sp.true or result is sp.S.EmptySet:
        return result
    if isinstance(variables, tuple):
        symbols=tuple(bare(v) for v in variables)
        variable=sp.Tuple(*symbols)
    else:
        symbols=(bare(variables),)
        variable=symbols[0]
    if isinstance(result, sp.FiniteSet):
        accepted=[]
        pending=[]
        for item in result:
            values=tuple(item) if isinstance(variables,tuple) else (item,)
            check=condition.xreplace(dict(zip(symbols,map(bare,values))))
            if check is sp.true:
                accepted.append(item)
            elif check is not sp.false:
                pending.append(item)
        if not pending:
            return sp.FiniteSet(*accepted)
        return sp.Union(sp.FiniteSet(*accepted),sp.ConditionSet(variable,condition,sp.FiniteSet(*pending)))
    if not isinstance(variables, tuple):
        pending=[]
        for term in sp.And.make_args(condition):
            if isinstance(term,sp.Contains) and term.args[0]==variable:
                if result.is_subset(term.args[1]) is not True:
                    result=result.intersect(term.args[1])
            elif isinstance(term,(sp.Equality,sp.Unequality)) and term.free_symbols=={variable}:
                zeros=sp.solveset(term.lhs-term.rhs,variable,domain=sp.S.Complexes)
                intersection=result.intersect(zeros)
                if isinstance(term,sp.Equality):result=intersection
                elif intersection is not sp.S.EmptySet:result=result-intersection
            elif isinstance(term,sp.logic.boolalg.Boolean) and term.free_symbols=={variable} and result.is_subset(sp.S.Reals) is True:
                try:result=result.intersect(term.as_set())
                except NotImplementedError:pending.append(term)
            else:
                pending.append(term)
        condition=sp.And(*pending)
    return sp.ConditionSet(variable, condition, result)


def solve_scalar(expression, variable, domain):
    if not isinstance(expression, (sp.Expr, sp.Equality)) or not expression.has(sp.Piecewise):
        return sp.solveset(expression, variable, domain=domain)
    if isinstance(expression,sp.Equality):
        expression=expression.lhs-expression.rhs
    folded=sp.piecewise_fold(expression)
    if not isinstance(folded,sp.Piecewise):
        return sp.solveset(folded, variable, domain=domain)
    # Resolve branches in their original order. SymPy's Piecewise solver
    # otherwise uses real intervals for complex equality guards.
    remaining=sp.true
    solutions=[]
    for value,test in folded.args:
        branch=sp.And(remaining,bare(test))
        solutions.append(with_domain(sp.solveset(value,variable,domain=domain),variable,branch))
        remaining=sp.And(remaining,sp.Not(bare(test)))
    return sp.Union(*solutions)


def intrinsic_system_domain(value, condition, *, analysis=False):
    if not isinstance(value,sp.Expr):return False
    symbols=bare(value).free_symbols | condition.free_symbols
    if len(symbols)!=1:return False
    variable=next(iter(symbols))
    if variable.name not in {'s','z'}:
        return False
    restrictions=sp.And.make_args(condition)
    if not all(isinstance(term,sp.Unequality) and term.free_symbols=={variable} for term in restrictions):
        return False
    try:
        denominator=sp.cancel(bare(value)).as_numer_denom()[1]
        # The origin is outside the unit circle. A Laurent spelling can
        # exclude it while the rational continuation has a value there.
        if analysis and variable.name=='z':denominator*=variable
        poles=sp.Poly(denominator,variable,domain='EX')
        for term in restrictions:
            num,den=sp.cancel(term.lhs-term.rhs).as_numer_denom()
            excluded=sp.Poly(num*den,variable,domain='EX').sqf_part()
            if excluded.is_zero or not poles.rem(excluded).is_zero:return False
        return True
    except sp.PolynomialError:
        return False


def scoped_result(command, args, domains):
    if command=='nsolve':
        return ()
    if command not in {'limit','integrate','int','sum','summation','prod','product','integral'} or len(args)<2:
        return domains
    # A pointwise exclusion at the bound variable is not an exclusion on the
    # returned scalar. For instance lim sin(x)/x at zero is defined.
    if command=='limit':
        if len(args)<3 or not isinstance(args[1],sp.Symbol):return domains
        variable=bare(args[1]);point=args[2]
        terms=sp.And.make_args(domains[0])
        required=[term for term in terms if variable in term.free_symbols and not isinstance(term,sp.Unequality)]
        if required:
            allowed=with_domain(sp.S.Reals,variable,sp.And(*required))
            left=point is sp.oo or point != -sp.oo and len(args)>3 and str(args[3])=='left'
            try:
                half=sp.Interval.open(-sp.oo,point) if left else sp.Interval.open(point,sp.oo)
                approach=allowed.intersect(half)
                edge=approach.sup if left else approach.inf
            except (TypeError,ValueError,NotImplementedError):edge=None
            if edge!=point:
                raise ValueError('El dominio de la expresión no permite verificar el límite por ese lado.')
        return [term for domain in domains for term in sp.And.make_args(domain) if variable not in term.free_symbols]
    limits=[tuple(args[1:])] if len(args)==4 and isinstance(args[1],sp.Symbol) else args[1:]
    restrictions=list(sp.And.make_args(domains[0]))
    for item in limits:
        if not isinstance(item,(tuple,list,sp.Tuple)) or len(item)!=3:
            continue
        variable,lower,upper=item
        if not isinstance(variable,sp.Symbol):
            continue
        local=[term for term in restrictions if bare(variable) in term.free_symbols]
        if not local:
            continue
        discrete=command in {'sum','summation','prod','product'}
        # Continuous definite integrals allow isolated point exclusions. The
        # interval still has to satisfy restrictions used to simplify its integrand.
        required=local if discrete else [term for term in local if not isinstance(term,sp.Unequality)]
        if required:
            start,stop=sp.Min(lower,upper),sp.Max(lower,upper)
            if discrete and start.is_integer is True and stop.is_integer is True:
                interval=sp.Range(start,stop+1)
            else:
                interval=sp.Interval(start,stop,left_open=not discrete,right_open=not discrete)
            allowed=with_domain(interval,variable,sp.And(*required))
            if interval!=allowed and interval.is_subset(allowed) is not True:
                raise ValueError('El intervalo del cálculo incluye puntos fuera del dominio de la expresión o no se pudo verificar.')
        restrictions=[term for term in restrictions if term not in local]
    return [*restrictions,*domains[1:]]
