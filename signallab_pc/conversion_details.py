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


def enrich_conversion(result,original,period,method,references=(),*,input_expression=None,reference_notice=None):
    from .auxiliary import optional
    notices=[reference_notice] if reference_notice else []
    def read_references():
        values=list(map(float,references))
        if any(not math.isfinite(v) or v<=0 for v in values):raise ValueError('Los cortes analógicos de referencia deben ser positivos y finitos, en rad/s.')
        return values
    checked,notice=optional('Cortes de referencia',read_references)
    references=checked or []
    if notice:notices.append(notice)
    forward=method in ('bilinear','impulse')
    source_measure,notice=optional('Cortes medidos de entrada',lambda:half_power(original,references)) if original is not None else (None,None)
    if notice:notices.append(notice)
    edges=references or (source_measure['frequencies'] if forward and source_measure else [])
    from .course_tools import map_analog_frequency
    mappings=[]
    for edge in edges:
        def mapping():
            raw=edge*period
            if not math.isfinite(raw):raise ValueError('Ωc·T excede el rango numérico.')
            mapped=abs(map_analog_frequency(edge,period,method))
            return {'analog':edge,'digital':mapped,'unwrapped':raw,'aliased':method=='impulse' and raw>math.pi}
        mapped,notice=optional('Mapeo del corte de referencia',mapping)
        if mapped is not None:mappings.append(mapped)
        if notice:notices.append(notice)
    info={'method':method,'period':float(period),'references_entered':bool(references),'mappings':mappings,'ideal':original is None,
          'input':_formula(original,'Ha' if original.domain=='analog' else 'Hd') if original is not None else {'expression':'Ha(w) = '+input_expression,'text':'Ha(w) = '+input_expression},
          'source_measurement':source_measure,'outputs':[],'base_report':result['report']}
    for index,system in enumerate(result['systems']):
        measurement,notice=optional('Cortes medidos de '+system.name,lambda:half_power(system))
        if notice:notices.append(notice)
        info['outputs'].append({'name':system.name,'domain':system.domain,'formula':_formula(system,'Hd' if system.domain=='digital' else 'Ha'+str(index+1)),
                                'measurement':measurement,'index':index})
    info['notices']=notices
    result['conversion_details']=info;result['report']=conversion_summary(info).plain_text()
    return result


def conversion_summary(info):
    method=info['method'];period=info['period']
    method_title={'bilinear':'Bilineal','impulse':'Invarianza al impulso','inverse':'Bilineal inversa','impulse_inverse':'Inversa de invarianza · candidatos'}.get(method,method)
    def definition(title,data):
        return Section(title,formulas=[Formula(data['expression'],data['text'])],rows=[('b',data['b']),('a',data['a'])] if 'b' in data else [])
    sections=[Section('Conversión realizada',rows=[('Método',method_title),('Período T (s)',number(period))])]
    for output in info['outputs']:
        sections.append(definition('Transferencia resultante · '+output['name'],output['formula']))
    sections.append(definition('Definición de entrada',info['input']))
    if method in ('bilinear','inverse'):
        formulas=[Formula('s = (2/T)*(z-1)/(z+1)','s = (2/T)·(z−1)/(z+1)'),Formula('z = (1+s*T/2)/(1-s*T/2)','z = (1+sT/2)/(1−sT/2)'),Formula('omega = 2*atan(Omega*T/2)','ω = 2·atan(ΩT/2)'),Formula('Omega = (2/T)*tan(omega/2)','Ω = (2/T)·tan(ω/2)')]
        paragraphs=[]
    else:
        formulas=[Formula('z = exp(s*T)','z = exp(sT)'),Formula('omega = Omega*T','ω = ΩT, módulo 2π')]
        paragraphs=['La relación exponencial corresponde a los polos.']
    sections.append(Section('Relación entre s y z',formulas=formulas,paragraphs=paragraphs))
    if info['mappings']:
        rows=[]
        for item in info['mappings']:
            text=number(item['digital'])+' rad/muestra'
            if method=='impulse' and item['aliased']:
                text+=' (plegado desde '+number(item['unwrapped'])+' rad/muestra)'
            rows.append(('Ωc = '+number(item['analog'])+' rad/s',text))
        basis='Se usaron los cortes analógicos ingresados.' if info['references_entered'] else 'Se usaron los cruces analógicos de media potencia (−3.01 dB).'
        sections.append(Section('Frecuencias de corte mapeadas',rows=rows,paragraphs=[basis]))
    elif method in ('bilinear','impulse'):
        sections.append(Section('Frecuencias de referencia',paragraphs=['El cálculo no encontró cortes por media potencia. Podés indicar los cortes de referencia en el formulario.']))
    for output in info['outputs']:
        measurement=output['measurement']
        if measurement is None:continue
        unit='rad/muestra' if output['domain']=='digital' else 'rad/s'
        rows=[('Cruces de media potencia',', '.join(number(v) for v in measurement['frequencies'])+' '+unit if measurement['frequencies'] else 'No detectados en el intervalo evaluado'),('Ganancia de referencia',number(measurement['reference_gain'])),('Intervalo evaluado',number(measurement['range'][0])+' … '+number(measurement['range'][1])+' '+unit)]
        title='Cortes medidos' if len(info['outputs'])==1 else 'Cortes medidos · '+output['name']
        sections.append(Section(title,rows=rows))
    if info.get('notices'):sections.append(Section('Mediciones complementarias no disponibles',paragraphs=info['notices']))
    if info.get('ideal') or method=='impulse_inverse':sections.append(Section('Alcance de la conversión',paragraphs=[info['base_report']]))
    return Summary('Conversión analógico / digital',sections)
