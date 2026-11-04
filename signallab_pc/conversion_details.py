"""Conversion equations, mapped reference edges and measured half-power crossings."""
import math
import numpy as np
from scipy.optimize import brentq
from .result_summary import Summary,Section,Formula,number
from .phase_summary import transfer_formula


def response_grid(system,references=()):
    if system.domain=='digital':
        return np.unique(np.r_[np.linspace(0,np.pi,4097),np.geomspace(1e-12,np.pi,2049)])
    zeros,poles=system.poles_zeros()
    scales=np.r_[abs(zeros),abs(poles),np.asarray(references,dtype=float)]
    scales=scales[np.isfinite(scales)&(scales>0)]
    low=float(np.min(scales))/1000 if scales.size else .01
    high=float(np.max(scales))*1000 if scales.size else 100.
    low=max(low,np.finfo(float).tiny);high=min(high,np.finfo(float).max/16)
    if not math.isfinite(high) or high<=low:raise ValueError('El rango de frecuencias del sistema no puede representarse con la precisión disponible.')
    return np.unique(np.r_[0,np.geomspace(low,high,4097),references])


def half_power(system,references=()):
    w=response_grid(system,references);h=system.response(w);magnitude=np.abs(h);valid=np.isfinite(magnitude)
    peak=float(np.max(magnitude[valid],initial=0));cuts=[]
    if system.domain=='analog':
        numerator=np.trim_zeros(system.b,'f')
        if len(numerator)==len(system.a):peak=max(peak,float(abs(numerator[0]/system.a[0])))
    result={'frequencies':cuts,'reference_gain':peak,'range':[float(w[0]),float(w[-1])],
            'definition':'Cruces a −3.0103 dB respecto de la ganancia de referencia: máximo de la rejilla, incluyendo el límite analógico conocido en infinito; no son bordes de especificación.'}
    if not peak:return result
    level=1/math.sqrt(2);difference=magnitude/peak-level
    for index in range(len(w)-1):
        if not valid[index] or not valid[index+1]:continue
        a,b=float(w[index]),float(w[index+1]);fa,fb=difference[index:index+2]
        if fa==0:root=a
        elif fa*fb<0:
            def target(omega):return float(abs(system.response(np.array([omega]))[0])/peak-level)
            try:
                root=brentq(target,a,b,xtol=np.nextafter(0.,1.),rtol=8*np.finfo(float).eps)
                if abs(target(root))>1e-6:continue
            except (ValueError,RuntimeError,OverflowError):continue
        elif fb==0:root=b
        else:continue
        if not cuts or abs(root-cuts[-1])>32*max(math.ulp(root),math.ulp(cuts[-1])):cuts.append(float(root))
    return result


def _formula(system,symbol):
    formula,compact=transfer_formula(system,symbol,digits=17)
    result={'expression':formula.expression,'text':formula.text}
    if compact:
        def coefficient(v):
            v=complex(v)
            return format(v.real,'.17g') if not v.imag else '('+format(v.real,'.17g')+'+i*('+format(v.imag,'.17g')+'))'
        result['b']=', '.join(coefficient(v) for v in system.b);result['a']=', '.join(coefficient(v) for v in system.a)
    return result


def enrich_conversion(result,original,period,method,references=(),*,input_expression=None):
    references=list(map(float,references))
    if any(not math.isfinite(v) or v<=0 for v in references):raise ValueError('Los cortes analógicos de referencia deben ser positivos y finitos, en rad/s.')
    forward=method in ('bilinear','impulse')
    source_measure=half_power(original,references) if original is not None else None
    edges=references or (source_measure['frequencies'] if forward and source_measure else [])
    from .course_tools import map_analog_frequency
    mappings=[]
    for edge in edges:
        raw=edge*period
        if not math.isfinite(raw):raise ValueError('Ωc·T excede el rango numérico; revisá el corte y el período.')
        mapped=abs(map_analog_frequency(edge,period,method))
        mappings.append({'analog':edge,'digital':mapped,'unwrapped':raw,'aliased':method=='impulse' and raw>math.pi})
    info={'method':method,'period':float(period),'references_entered':bool(references),'mappings':mappings,'ideal':original is None,
          'input':_formula(original,'Ha' if original.domain=='analog' else 'Hd') if original is not None else {'expression':'Ha(w) = '+input_expression,'text':'Ha(w) = '+input_expression},
          'source_measurement':source_measure,'outputs':[],'base_report':result['report']}
    for index,system in enumerate(result['systems']):
        info['outputs'].append({'name':system.name,'domain':system.domain,'formula':_formula(system,'Hd' if system.domain=='digital' else 'Ha'+str(index+1)),
                                'measurement':half_power(system),'index':index})
    result['conversion_details']=info;result['report']=conversion_summary(info).plain_text()
    return result


def conversion_summary(info):
    method=info['method'];period=info['period']
    method_title={'bilinear':'Bilineal','impulse':'Invarianza al impulso','inverse':'Bilineal inversa','impulse_inverse':'Inversa de invarianza · candidatos'}.get(method,method)
    def definition(title,data):
        return Section(title,formulas=[Formula(data['expression'],data['text'])],rows=[('b',data['b']),('a',data['a'])] if 'b' in data else [])
    sections=[Section('Método',rows=[('Transformación',method_title),('Período T (s)',number(period))]),definition('Definición de entrada',info['input'])]
    if method in ('bilinear','inverse'):
        formulas=[Formula('s = (2/T)*(z-1)/(z+1)','s = (2/T)·(z−1)/(z+1)'),Formula('z = (1+s*T/2)/(1-s*T/2)','z = (1+sT/2)/(1−sT/2)'),Formula('omega = 2*atan(Omega*T/2)','ω = 2·atan(ΩT/2)'),Formula('Omega = (2/T)*tan(omega/2)','Ω = (2/T)·tan(ω/2)')]
        paragraphs=['La sustitución relaciona las transferencias completas. Comprime el eje analógico infinito dentro de −π<ω<π. El mapeo no introduce aliasing; la frecuencia se deforma.']
    else:
        formulas=[Formula('z = exp(s*T)','z = exp(sT)'),Formula('omega = Omega*T','ω = ΩT, módulo 2π')]
        paragraphs=['El mapeo exponencial relaciona los polos; no se obtiene toda H(z) sustituyendo s por log(z)/T en H(s). Se usa h[n]=T·ha(nT). Las réplicas espectrales pueden producir aliasing y cambiar el corte efectivo. La transformación inversa tiene distintas ramas.']
    sections.append(Section('Relación entre s y z',formulas=formulas,paragraphs=paragraphs))
    if info['mappings']:
        rows=[]
        for item in info['mappings']:
            text=number(item['digital'])+' rad/muestra'
            if method=='impulse':text+=' · ΩcT = '+number(item['unwrapped'])+(' rad/muestra; plegado por aliasing' if item['aliased'] else ' rad/muestra, sin plegado')
            rows.append(('Ωc = '+number(item['analog'])+' rad/s',text))
        sections.append(Section('Frecuencias de corte mapeadas',rows=rows,paragraphs=['Se usan los cortes analógicos ingresados.' if info['references_entered'] else 'Se usan los cruces analógicos detectados a −3.0103 dB respecto del máximo evaluado.','En invarianza al impulso, el corte mapeado es una referencia. Los cruces del filtro obtenido se muestran por separado.'] if method=='impulse' else ['Se usan los cortes analógicos ingresados.' if info['references_entered'] else 'Se usan los cruces analógicos detectados a −3.0103 dB respecto del máximo evaluado.']))
    elif method in ('bilinear','impulse'):
        sections.append(Section('Frecuencias de referencia',paragraphs=['No se detectaron cortes analógicos con el criterio automático. Podés indicar uno o varios Ωc de referencia en el formulario; ese dato sólo se usa para mostrar el mapeo y no modifica el filtro.']))
    for output in info['outputs']:
        sections.append(definition('Transferencia resultante · '+output['name'],output['formula']))
        measurement=output['measurement'];unit='rad/muestra' if output['domain']=='digital' else 'rad/s'
        rows=[('Cruces de media potencia',', '.join(number(v) for v in measurement['frequencies'])+' '+unit if measurement['frequencies'] else 'No detectados en el intervalo evaluado'),('Ganancia de referencia',number(measurement['reference_gain'])),('Intervalo evaluado',number(measurement['range'][0])+' … '+number(measurement['range'][1])+' '+unit)]
        sections.append(Section('Cortes medidos en el resultado',rows=rows,paragraphs=['Se busca |H|=referencia/√2, equivalente a −3.0103 dB. La referencia toma el máximo de la rejilla y, para H(s), su límite conocido en infinito si es mayor. Este criterio de media potencia no equivale a cualquier borde de tolerancia de un diseño. La rejilla y el refinamiento numérico pueden omitir cruces muy estrechos.']))
    if info.get('ideal') or method=='impulse_inverse':sections.append(Section('Alcance de la conversión',paragraphs=[info['base_report']]))
    sections.append(Section('Lectura y uso',paragraphs=['Los cortes de referencia sólo muestran el mapeo: no rediseñan ni predeforman la transferencia ingresada. El módulo puede verse en amplitud lineal o en dB desde los controles del resultado y desde la barra del gráfico. La transferencia calculada puede exportarse o reutilizarse en las demás herramientas.']))
    return Summary('Conversión analógico / digital',sections)
