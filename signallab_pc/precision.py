"""Exact encoding and coefficient storage quantization; arithmetic stays separate."""
from dataclasses import dataclass
from fractions import Fraction
import math
import numpy as np
from .filters import Transfer
from .resources import ensure_working_set
from .jobs import checkpoint


def ratio_text(value):
    if max(abs(value.numerator).bit_length(),value.denominator.bit_length())<3000:return str(value)
    return hex(value.numerator)+' / '+hex(value.denominator)


def _rounded(value,even=True):
    q,r=divmod(value.numerator,value.denominator)
    return q+int(2*r>value.denominator or 2*r==value.denominator and (not even or q%2))


def _power(value,exponent):
    return value*(1<<exponent) if exponent>=0 else value/Fraction(1<<-exponent)


@dataclass(frozen=True)
class Encoding:
    kind:str='fixed'
    integer_bits:int=2
    fractional_bits:int=14
    rounding:str='round'
    def __post_init__(self):
        if self.kind not in ('fixed','float16','float32','float64'):raise ValueError('Elegí punto fijo o binary16, binary32 o binary64.')
        if self.kind=='fixed':
            if isinstance(self.integer_bits,bool) or int(self.integer_bits)!=self.integer_bits or self.integer_bits<1:raise ValueError('Los bits enteros incluyen el signo y deben ser positivos.')
            if isinstance(self.fractional_bits,bool) or int(self.fractional_bits)!=self.fractional_bits or self.fractional_bits<0:raise ValueError('Los bits fraccionarios deben ser enteros no negativos.')
            object.__setattr__(self,'integer_bits',int(self.integer_bits));object.__setattr__(self,'fractional_bits',int(self.fractional_bits))
            ensure_working_set(self.width,bytes_per_sample=1,live_arrays=32)
        if self.rounding not in ('round','truncate'):raise ValueError('Elegí redondeo o truncamiento.')
    @property
    def width(self):return self.integer_bits+self.fractional_bits if self.kind=='fixed' else int(self.kind[5:])
    @property
    def name(self):return f'Q({self.integer_bits},{self.fractional_bits})' if self.kind=='fixed' else 'IEEE 754 binary'+str(self.width)
    def encode(self,source,negative_zero=False):
        source=Fraction(source);sign=source<0 or source==0 and negative_zero;x=abs(source);classification='normal';clipped=False
        if self.kind=='fixed':
            scale=1<<self.fractional_bits;minimum=-(1<<(self.width-1));maximum=(1<<(self.width-1))-1
            scaled=source*scale;limited=min(Fraction(maximum),max(Fraction(minimum),scaled));clipped=limited!=scaled
            magnitude=abs(limited);code=_rounded(magnitude,False) if self.rounding=='round' else magnitude.numerator//magnitude.denominator
            if limited<0:code=-code
            value=Fraction(code,scale);bits=code%(1<<self.width);classification='saturado' if clipped else 'cero' if code==0 else 'representado'
            result={'value':value,'word':format(bits,'0'+str(self.width)+'b'),'hex':hex(bits),'classification':classification,'saturated':clipped,'code':str(code) if abs(code).bit_length()<3000 else hex(code),'sign':int(sign)}
        else:
            eb,fb={16:(5,10),32:(8,23),64:(11,52)}[self.width];bias=(1<<(eb-1))-1;emin=1-bias;emax=bias
            if x:
                exponent=x.numerator.bit_length()-x.denominator.bit_length()
                if _power(x,-exponent)<1:exponent-=1
                if exponent<emin:
                    significand=_rounded(_power(x,fb-emin));ef=1 if significand>=(1<<fb) else 0;fraction=significand-(1<<fb) if ef else significand
                    magnitude=_power(Fraction(significand),emin-fb);classification='normal' if ef else 'subnormal' if significand else 'cero'
                else:
                    significand=_rounded(_power(x,fb-exponent))
                    if significand==(1<<(fb+1)):significand>>=1;exponent+=1
                    if exponent>emax:ef=(1<<eb)-1;fraction=0;magnitude=None;classification='desborde a infinito'
                    else:ef=exponent+bias;fraction=significand-(1<<fb);magnitude=_power(Fraction(significand),exponent-fb)
            else:ef=0;fraction=0;magnitude=Fraction(0);classification='cero'
            bits=(int(sign)<<(self.width-1))|(ef<<fb)|fraction
            result={'value':(-magnitude if sign else magnitude) if magnitude is not None else None,'word':format(bits,'0'+str(self.width)+'b'),'hex':hex(bits),'classification':classification,'saturated':False,'sign':int(sign),'exponent_bits':format(ef,'0'+str(eb)+'b'),'fraction_bits':format(fraction,'0'+str(fb)+'b')}
        return result


def represent(source,encoding):
    from .cas_engine import Calculator,empty_state
    from decimal import Decimal,InvalidOperation
    import sympy as sp
    expression=Calculator(empty_state()).parse(source)
    if not isinstance(expression,sp.Expr) or expression.free_symbols or expression.is_real is not True or expression.is_finite is not True:raise ValueError('Ingresá una constante real finita, sin variables.')
    exact=expression.is_Rational
    reference=Fraction(int(expression.p),int(expression.q)) if exact else Fraction(str(sp.N(expression,100)))
    negative_zero=False
    try:decimal=Decimal(source.strip());negative_zero=decimal.is_zero() and decimal.is_signed()
    except InvalidOperation:pass
    result=encoding.encode(reference,negative_zero);value=result.pop('value')
    result.update(format=encoding.name,input=source,reference_exact=bool(exact),represented_exact=ratio_text(value) if value is not None else ('−∞' if result['sign'] else '+∞'),error_exact=ratio_text(value-reference) if value is not None else None,reference_note='La entrada se interpreta como un racional exacto.' if exact else 'La constante se aproxima con 100 cifras decimales antes de codificar; el error se refiere a esa referencia.')
    if value is not None:
        result['represented_approx']=str(sp.N(sp.Rational(value.numerator,value.denominator),18))
        error=value-reference;result['error_approx']=str(sp.N(sp.Rational(error.numerator,error.denominator),18))
    return result


def quantize_coefficients(system,encoding,preserve_sections=True):
    if system.advance:raise ValueError('Este estudio utiliza una realización causal. El sistema con avance se puede analizar sin cambiar su fórmula en Análisis de sistemas.')
    if system.domain!='digital':raise ValueError('Esta comparación de coeficientes utiliza H(z).')
    sections=system.sos is not None and preserve_sections
    size=system.sos.size if sections else len(system.b)+len(system.a)
    ensure_working_set(int(size*max(encoding.width,64)),bytes_per_sample=1,live_arrays=16)
    rows=[]
    def convert(value,label):
        value=complex(value);output=[]
        for component,suffix in [(value.real,'real'),(value.imag,'imag')]:
            encoded=encoding.encode(Fraction.from_float(component),component==0 and math.copysign(1,component)<0)
            if encoded['value'] is None:raise ValueError(label+' excede el formato flotante. Elegí un formato de mayor rango; no se crea un filtro con coeficientes infinitos.')
            try:stored=float(encoded['value'])
            except OverflowError:raise ValueError('El coeficiente redondeado no puede almacenarse en doble precisión.')
            if not math.isfinite(stored):raise ValueError('El coeficiente redondeado no es finito en el motor numérico.')
            output.append(stored)
            if suffix=='real' or component!=0 or value.imag!=0:
                rows.append({'coefficient':label,'component':suffix,'original':component,'stored':stored,'error':stored-component,'word':encoded['word'],'hex':encoded['hex'],'classification':encoded['classification'],'saturated':encoded['saturated']})
        return complex(*output)
    if sections:
        data=system.sos.copy()
        for section,row in enumerate(data):
            checkpoint()
            for k in range(6):
                if k==3:continue
                data[section,k]=convert(row[k],f'S{section+1} · '+('b' if k<3 else 'a')+str(k if k<3 else k-3)).real
        result=Transfer.from_sos(data,'Filtro con coeficientes '+encoding.name,sample_period_s=system.sample_period_s)
    else:
        b=[convert(value,'b['+str(k)+']') for k,value in enumerate(system.b)]
        a=[1]+[convert(value,'a['+str(k)+']') for k,value in enumerate(system.a[1:],1)]
        result=Transfer(b,a,'digital','Filtro con coeficientes '+encoding.name,sample_period_s=system.sample_period_s)
    def denominator_poles(model):
        if model.sos is not None:return np.concatenate([np.roots(row[3:]) for row in model.sos])
        ensure_working_set(len(model.a)**2,live_arrays=8)
        return np.roots(model.a)
    original_poles=denominator_poles(system);stored_poles=denominator_poles(result)
    w=np.linspace(0,np.pi,4097);original=system.response(w);stored=result.response(w);valid=np.isfinite(original)&np.isfinite(stored)
    # Scale before subtracting to avoid overflow where only the relative error fits.
    maximum=max(1.,float(np.max(abs(original[valid].real),initial=0)),float(np.max(abs(original[valid].imag),initial=0)),float(np.max(abs(stored[valid].real),initial=0)),float(np.max(abs(stored[valid].imag),initial=0)))
    error=stored/maximum-original/maximum;finite_error=error[valid]
    metrics={'changed':sum(row['original']!=row['stored'] for row in rows),'saturated':sum(row['saturated'] for row in rows),'components':len(rows),'response_scale':maximum,'scaled_response_error_max':float(np.max(abs(finite_error))) if len(finite_error) else None,'undefined_points':int(np.count_nonzero(~valid)),
        'original_pole_radius':float(np.max(abs(original_poles),initial=0)),'stored_pole_radius':float(np.max(abs(stored_poles),initial=0)),'original_poles':system.stability(original_poles),'stored_poles':result.stability(stored_poles)}
    return {'source':system,'system':result,'encoding':encoding,'sections':bool(sections),'rows':rows,'omega':w,'original_response':original,'stored_response':stored,'metrics':metrics}


def precision_summary(data):
    from .result_summary import Summary,Section,Formula,number
    from .phase_summary import transfer_formula
    if 'system' not in data:
        shown_value=data['represented_exact'] if len(data['represented_exact'])<=50 else data.get('represented_approx',data['represented_exact'])+' (aproximado; exacto en JSON)'
        shown_error=data['error_exact'] if data['reference_exact'] and data['error_exact'] is not None and len(data['error_exact'])<=50 else data.get('error_approx','No definido por desborde')
        rows=[('Entrada',data['input']),('Formato',data['format']),('Clase',data['classification']),('Valor representado',shown_value),('Error salida − referencia'+(' (aproximado)' if shown_error!=data['error_exact'] and data['error_exact'] is not None else ''),shown_error),('Palabra hexadecimal',data['hex'])]
        bits=data['word'];rows.append(('Palabra binaria',bits if len(bits)<=128 else bits[:48]+'…'+bits[-48:]+' (vista abreviada)'))
        if 'exponent_bits' in data:rows.extend([('Signo',str(data['sign'])),('Exponente almacenado',data['exponent_bits']),('Fracción almacenada',data['fraction_bits'])])
        else:rows.append(('Código con signo',data['code']))
        return Summary('Representación numérica',[Section('Resultado',rows=rows),Section('Referencia y redondeo',paragraphs=[data['reference_note'],'Punto fijo usa complemento a dos, saturación y el redondeo o truncamiento elegidos. IEEE 754 usa redondeo al más cercano con empates al par, incluidos subnormales y cero con signo. La palabra completa se conserva al exportar el resultado.'])])
    metrics=data['metrics'];formula,compact=transfer_formula(data['system'],'Hq')
    sections=[Section('Filtro cuantizado',formulas=[formula],paragraphs=['Se cuantiza el almacenamiento de los coeficientes normalizados de H(z). a[0]=1 es una constante implícita de la recurrencia y no se redondea ni satura.'])]
    if compact:sections.append(Section('Coeficientes de la fórmula',rows=[('b[k]',', '.join(number(v) for v in data['system'].b)),('a[k]',', '.join(number(v) for v in data['system'].a))]))
    sections+=[Section('Formato y realización',rows=[('Formato',data['encoding'].name),('Estructura','Cascada SOS conservada' if data['sections'] else 'Polinomios directos'),('Componentes cuantizadas',metrics['components']),('Componentes modificadas',metrics['changed']),('Saturaciones',metrics['saturated'])]),
        Section('Efecto sobre los polos',rows=[('Radio máximo original',number(metrics['original_pole_radius'])),('Radio máximo cuantizado',number(metrics['stored_pole_radius'])),('Polos originales',metrics['original_poles']),('Polos cuantizados',metrics['stored_poles'])],paragraphs=['Se comparan los polos del denominador, sin cancelar ceros próximos. Un polo sobre el círculo unidad no es estrictamente estable. Una transferencia externa con cancelaciones puede ocultar modos internos.']),
        Section('Efecto sobre la respuesta',rows=[('Escala de comparación S',number(metrics['response_scale'])),('Máximo |Hq−H|/S en la rejilla',number(metrics['scaled_response_error_max']) if metrics['scaled_response_error_max'] is not None else 'No hay puntos comunes finitos'),('Puntos no definidos',metrics['undefined_points'])],paragraphs=['S es la mayor componente real o imaginaria en valor absoluto de ambas respuestas finitas, con mínimo uno. Esta normalización evita desbordes y no es un error relativo punto a punto. Se evalúan 4097 frecuencias entre 0 y π rad/muestra, sin garantizar máximos entre todos los puntos.']),
        Section('Qué representa esta comparación',paragraphs=['Los coeficientes cuantizados se evalúan después con el motor de doble precisión. No se redondean productos, sumas, acumuladores ni estados durante la ejecución: esta opción estudia almacenamiento de coeficientes, no ruido aritmético ni ciclos límite de una implementación completa.',
        'Si se conservan SOS, se redondea cada sección y se mantiene su orden. Elegir polinomios directos expande la definición y puede aumentar la sensibilidad numérica. Los coeficientes de entrada se toman de los valores binarios almacenados en el sistema, no de una constante exacta anterior desconocida.',
        'La tabla y el CSV muestran las conversiones y saturaciones. Exportar o reutilizar toma el filtro cuantizado del último cálculo, aunque después se editen los datos.'])]
    return Summary('Precisión de los coeficientes',sections)
