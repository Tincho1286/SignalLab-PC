"""High precision pole values and direct numerical expressions for inverses."""
import mpmath as mp
import sympy as sp
from .partial_fractions import apart_list
from .signal_notation import SignalPrinter,normalize


class PoleValues:
    def __init__(self):self.context=mp.mp.clone();self.context.dps=80;self.values={}
    def value(self,value):
        if value in self.values:return self.values[value]
        real,imag=sp.N(value,85).as_real_imag()
        return self.context.mpc(str(real),str(imag))
    def match(self,factor,roots):
        context=self.context;candidates=[self.value(v) for v in factor.nroots(n=85,maxsteps=200)];values={}
        def rational(q):
            q=sp.Rational(q);return context.mpf(int(q.p))/int(q.q)
        for root in roots:
            if isinstance(root,sp.CRootOf):
                interval=root._get_interval()
                for _ in range(40):
                    if root.is_real:matches=[v for v in candidates if v.imag==0 and rational(interval.a)<=v.real<=rational(interval.b)]
                    else:matches=[v for v in candidates if rational(interval.ax)<=v.real<=rational(interval.bx) and rational(interval.ay)<=v.imag<=rational(interval.by)]
                    if len(matches)==1:break
                    interval=interval.refine()
                if len(matches)!=1:raise ValueError('No se pudo identificar una raíz numérica dentro de su intervalo algebraico exacto.')
                values[root]=matches[0]
            else:
                value=self.value(root);candidate=min(candidates,key=lambda item:abs(item-value))
                if abs(candidate-value)>context.mpf('1e-65')*max(1,abs(value)):raise ValueError('No se alcanzó suficiente precisión para identificar un polo.')
                values[root]=candidate
        return values
    def number(self,value):
        value=self.context.mpf(value)
        if value==0:return sp.S.Zero
        integer=int(value)
        if value==integer and abs(integer)<1000000:return sp.Integer(integer)
        digits=17
        text=self.context.nstr(value,digits)
        # Do not make a near-unit pole look exactly on the stability boundary.
        while self.context.mpf(text) in (0,1,-1) and self.context.mpf(text)!=value and digits<77:
            digits+=10;text=self.context.nstr(value,digits)
        return sp.Float(text,digits)
    def complex_number(self,value):return self.number(value.real)+sp.I*self.number(value.imag)


class NumericPrinter(SignalPrinter):
    def _print_Float(self,value):
        text=super()._print_Float(value);mantissa,separator,exponent=text.lower().partition('e')
        if '.' in mantissa:mantissa=mantissa.rstrip('0').rstrip('.')
        return mantissa+(separator+exponent if separator else '')


def expression_source(expression):return NumericPrinter({'order':'none'}).doprint(normalize(expression))


def modal_expression(terms,variable,values,kind='z',real_input=False,with_terms=False):
    """Pair proven numerical conjugates, keeping support and repeated-pole order."""
    context=values.context;used=set();groups={};fragments=[];tolerance=context.mpf('1e-60')
    for index,term in enumerate(terms):
        if index in used:continue
        p,c,order=term['pole'],term['coefficient'],term['order'];right=term.get('right',True)
        condition=(variable>=order if right else variable<=0) if kind=='z' else right
        argument=variable-order if kind=='z' else variable
        partner=None
        if real_input and p.imag:
            for other_index,other in enumerate(terms):
                if other_index==index or other_index in used or other['order']!=order or other.get('right',True)!=right:continue
                if abs(other['pole']-p.conjugate())<=tolerance*max(1,abs(p)) and abs(other['coefficient']-c.conjugate())<=tolerance*max(1,abs(c)):
                    partner=other_index;break
        if partner is not None:
            if p.imag<0:p,c=terms[partner]['pole'],terms[partner]['coefficient']
            if kind=='z':scale=values.number(abs(p))**argument;angle=values.number(context.arg(p))*argument
            else:scale=sp.exp(values.number(p.real)*variable);angle=values.number(p.imag)*variable
            pieces=[2*scale*values.number(c.real)*sp.cos(angle),-2*scale*values.number(c.imag)*sp.sin(angle)]
            mode=sp.Add(*pieces);used.add(partner)
        else:
            if kind=='z':mode=values.complex_number(c)*values.complex_number(p)**argument
            else:mode=values.complex_number(c)*sp.exp(values.complex_number(p)*variable)
            pieces=[mode]
        if kind=='z':weight=sp.binomial(variable-1,order-1) if right else (-1)**order*sp.binomial(order-variable-1,order-1)
        else:weight=variable**(order-1)/sp.factorial(order-1)
        groups.setdefault(condition,[]).append(weight*mode);used.add(index)
        for piece in pieces:
            if piece!=0:fragments.append((1 if right else -1)*weight*piece*sp.Heaviside(variable if right else -variable) if kind=='laplace' else sp.Piecewise((weight*piece,condition),(0,True),evaluate=False))
    result=sp.Add(*[(1 if side else -1)*sp.Add(*items)*sp.Heaviside(variable if side else -variable) for side,items in groups.items()]) if kind=='laplace' else sp.Add(*[sp.Piecewise((sp.Add(*items),condition),(0,True),evaluate=False) for condition,items in groups.items()])
    return (result,fragments) if with_terms else result


def laplace_numeric(value,variable,time):
    """Only hard, numeric rational cases; elementary/symbolic cases keep the CAS path."""
    if value.free_symbols-{variable}:return None
    try:
        rational=sp.cancel(value);num,den=map(lambda v:sp.Poly(v,variable),sp.fraction(rational))
        if den.degree()<=2:return None
        common,polynomial,parts=apart_list(rational,variable)
    except (sp.PolynomialError,NotImplementedError):return None
    if not any(factor.degree()>2 for factor,coefficient,denominator,order in parts):return None
    from .resources import ensure_working_set
    from .jobs import checkpoint
    ensure_working_set(max(1,int(den.degree())**2),bytes_per_sample=1024,live_arrays=8)
    values=PoleValues();terms=[];root_cache={}
    for factor,coefficient,denominator,order in parts:
        if coefficient.expr==0:continue
        dummy=denominator.variables[0]
        if sp.expand(denominator.expr-(variable-dummy))!=0:raise ValueError('No se pudo normalizar una fracción parcial de Laplace.')
        key=factor.as_expr()
        if key not in root_cache:root_cache[key]=[values.value(v) for v in factor.nroots(n=85,maxsteps=200)]
        for pole in root_cache[key]:
            checkpoint();point=sp.Float(str(pole.real),85)+sp.I*sp.Float(str(pole.imag),85)
            c=values.value(common*coefficient(point))
            terms.append({'pole':pole,'coefficient':c,'order':int(order)})
    real_input=all(c.is_real is True for c in num.all_coeffs()+den.all_coeffs())
    result,fragments=modal_expression(terms,time,values,'laplace',real_input,with_terms=True)
    for (power,),coefficient in polynomial.terms():
        if coefficient:
            impulse=common*coefficient*sp.DiracDelta(time,power);result+=impulse;fragments.append(impulse)
    text=expression_source(result)
    decomposition=([str(common*polynomial.as_expr())] if not polynomial.is_zero else [])+['('+str(values.complex_number(item['coefficient']))+')/('+str(variable)+'-('+str(values.complex_number(item['pole']))+'))^'+str(item['order']) for item in terms]
    return {'decomposition':'+'.join(decomposition) or '0','operation':'Laplace inversa','result':text,'display_result':text,'display_terms':[expression_source(term) for term in fragments],'output_variable':'t','evaluated':True,'display_numeric':True,'display_precision':17,
        'scope':'Inversa causal: cero para t<0. Los polos y coeficientes se evalúan con precisión ampliada. El texto completo conserva al menos 17 cifras significativas; es una aproximación numérica de la función racional de entrada. La vista redondeada facilita su lectura. Esta operación no selecciona otras ROC bilaterales.'}
