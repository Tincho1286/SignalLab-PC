"""Mathematical definitions of calculated transfer functions and phase factors."""
import numpy as np
from .result_summary import Summary,Section,Formula,number


def transfer_formula(system,symbol='H',digits=12):
    """Keep the stored power convention; use finite sums for long expressions."""
    digital=system.domain=='digital';variable='z' if digital else 's'
    def polynomial(coefficients):
        terms=[]
        for index,value in enumerate(coefficients):
            value=complex(value)
            if value==0:continue
            power=-index if digital else len(coefficients)-index-1
            factor='' if power==0 else variable if power==1 else variable+'^('+str(power)+')'
            if not value.imag:
                sign='-' if value.real<0 else '+';coefficient=format(abs(value.real),'.'+str(digits)+'g')
                term=factor if factor and abs(value.real)==1 else coefficient+('*'+factor if factor else '')
            else:
                sign='+';real=format(value.real,'.'+str(digits)+'g');imag=format(abs(value.imag),'.'+str(digits)+'g')
                coefficient='('+real+('+' if value.imag>=0 else '-')+imag+'*i)';term=coefficient+('*'+factor if factor else '')
            terms.append((sign,term))
        return ''.join((sign if index else '-' if sign=='-' else '')+term for index,(sign,term) in enumerate(terms)) or '0'
    numerator=polynomial(system.b);denominator=polynomial(system.a)
    shift='z^('+str(system.advance)+')*' if system.advance else ''
    expanded=symbol+'('+variable+') = '+shift+'('+numerator+')/('+denominator+')'
    compact=len(numerator)+len(denominator)>180 or np.count_nonzero(system.b)+np.count_nonzero(system.a)>8
    if compact:
        def definition(coefficients,name):
            if len(coefficients)==1:return polynomial(coefficients)
            exponent='-k' if digital else str(len(coefficients)-1)+'-k'
            return 'Sum('+name+'[k]*'+variable+'^('+exponent+'),(k,0,'+str(len(coefficients)-1)+'))'
        numerator=definition(system.b,'b');denominator=definition(system.a,'a')
    expression=symbol+'('+variable+') = '+shift+'('+numerator+')/('+denominator+')'
    return Formula(expression,expanded),compact


def phase_summary(original,systems,selected,report):
    value=systems[selected];symbol='Hm' if selected==0 else 'Hap'
    formula,compact=transfer_formula(value,symbol)
    sections=[Section('Sistema seleccionado · '+value.name,formulas=[formula])]
    if compact:sections.append(Section('Coeficientes de la fórmula',paragraphs=['La suma finita conserva todos los términos. b[k] y a[k] son los coeficientes del resultado seleccionado, desde k=0.']))
    sections.append(Section('Valores del resultado seleccionado',rows=[('Numerador b',', '.join(number(v) for v in value.b)),('Denominador a',', '.join(number(v) for v in value.a))]))
    sections.append(Section('Factorización obtenida',paragraphs=['Hm refleja los ceros exteriores al interior del círculo unidad. Hap reúne el factor paso todo y el retardo. El selector elige el factor que se grafica, exporta o reutiliza.'],formulas=[Formula('H(z) = Hm(z)*Hap(z)','H(z) = Hm(z) · Hap(z)')]))
    other=1-selected
    other_formula,other_compact=transfer_formula(systems[other],'Hm' if other==0 else 'Hap')
    def coefficients(value):return [('b[k]',', '.join(number(v) for v in value.b)),('a[k]',', '.join(number(v) for v in value.a))]
    sections.append(Section('Otro factor · '+systems[other].name,rows=coefficients(systems[other]) if other_compact else [],formulas=[other_formula]))
    if original is not None:
        original_formula,original_compact=transfer_formula(original,'H')
        sections.append(Section('Sistema de entrada',rows=coefficients(original) if original_compact else [],formulas=[original_formula]))
    paragraphs=[line for line in report.split('\n\n')[1:] if line.strip()]
    sections.append(Section('Clasificación y alcance',paragraphs=['La comprobación de fase lineal y simetría corresponde al sistema de entrada. La condición estricta de fase mínima depende también de polos, ceros sobre el círculo y retardo.',*paragraphs]))
    sections.append(Section('Precisión',paragraphs=['Las fórmulas y tablas muestran hasta 12 cifras significativas de los coeficientes calculados. La exportación y la reutilización conservan los valores almacenados. Para fórmulas largas, la vista usa la notación de suma finita con b[k] y a[k] del sistema indicado; Copiar texto y Guardar texto incluyen el polinomio desarrollado.']))
    return Summary('Resultado de ajustar fase',sections)
