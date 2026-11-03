"""A transform input retains its support, exact values and completion policy."""
from dataclasses import dataclass
from copy import deepcopy
import sympy as sp
from .calculation_notes import capture


@dataclass(frozen=True)
class Definition:
    source:str
    expression:sp.Expr
    variable:sp.Symbol
    domain:str
    support:tuple|None=None
    support_kind:str='signal_support'
    extensions:tuple=()
    conditions:tuple=()

    def metadata(self):
        from .cas_engine import encode
        return {'schema_version':1,'source':self.source,'effective_expression':str(self.expression),
            'encoded_expression':encode(self.expression),'variable':str(self.variable),'domain':self.domain,
            'support':{'lower':str(self.support[0]),'upper':str(self.support[1]),'kind':self.support_kind} if self.support else None,
            'extensions':deepcopy(list(self.extensions)),'input_conditions':list(self.conditions),
            'extension_policy':'finite_equal_two_sided_real_limits','outside_support':'zero' if self.support_kind=='signal_support' and self.support else None}

    def integral_expression(self):
        """Isolated ordinary point values have zero measure, unlike impulses."""
        def strip(piece):
            if piece.has(sp.DiracDelta) or piece.args[-1].cond is not sp.true or any(condition.free_symbols-{self.variable} for _,condition in piece.args):return piece
            kept=[]
            for value,condition in piece.args:
                if condition is not sp.true:
                    try:region=condition.as_set()
                    except (NotImplementedError,ValueError,TypeError):region=None
                    if isinstance(region,sp.FiniteSet):continue
                kept.append((value,condition))
            return sp.Piecewise(*kept) if kept else piece
        value=self.expression.replace(lambda v:isinstance(v,sp.Piecewise),strip)
        # Exact rational cancellation is valid almost everywhere for ordinary
        # integrals. Distribution coefficients keep their explicit definition.
        return value if value.has(sp.DiracDelta) else sp.factor_terms(sp.cancel(value))


def prepare(source,variable,domain,support=None,conditions=(),support_kind='signal_support'):
    from .symbolic import parse
    from .singularities import resolve_finite_support
    with capture() as records:
        expression=parse(source)
        if domain=='discrete' and support is not None:
            expression=resolve_finite_support(expression,variable,*support)
            # Reject actual undefined integer samples, not real poles between
            # samples. Finite explicit values in Piecewise take precedence.
            real=sp.Dummy('coordinate',real=True)
            try:points=sp.singularities(expression.xreplace({variable:real}),real,domain=sp.S.Reals)
            except (NotImplementedError,ValueError,TypeError):points=sp.S.EmptySet
            if isinstance(points,sp.FiniteSet):
                lo,hi=support
                for point in points:
                    if point.is_integer is not True or (point>=lo) is sp.false or (point<=hi) is sp.false:continue
                    if (point>=lo) is not sp.true or (point<=hi) is not sp.true:continue
                    value=expression.subs(variable,point)
                    if value.has(sp.nan,sp.zoo,sp.oo,-sp.oo):raise ValueError('La secuencia no tiene un valor finito en '+str(variable)+'='+str(point)+'. No es una indeterminación removible; definí esa muestra explícitamente por tramos o corregí el soporte.')
        if not expression.free_symbols and expression.has(sp.nan,sp.zoo,sp.oo,-sp.oo):raise ValueError('La entrada no representa una expresión finita definida.')
    return Definition(str(source),expression,variable,domain,support,support_kind,tuple(dict(r) for r in records.values()),tuple(map(str,conditions)))


def attach(result,definition):
    result['input_definition']=definition.metadata()
    if definition.extensions:
        from .transform_status import merge_notes
        result['calculation_notes']=merge_notes(result.get('calculation_notes',[]),definition.extensions)
    from .transform_status import finalize
    return finalize(result)
