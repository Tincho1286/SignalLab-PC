"""Explicit digital phase adjustments and the cascade factor of each result."""
import numpy as np
from .filters import Transfer
from .resources import ensure_working_set


def _input(system):
    if system.domain!='digital':raise ValueError('El ajuste de fase trabaja con H(z).')
    b=np.trim_zeros(system.b,'b');a=np.trim_zeros(system.a,'b')
    if not b.size:raise ValueError('La transferencia nula no tiene fase ni inversa definidas.')
    ensure_working_set(int(max(len(a),len(b))**2),live_arrays=14)
    return b,a


def factor_phase(system):
    b,a=_input(system);delay=int(np.flatnonzero(b!=0)[0]);active=b[delay:]
    zeros=np.roots(active);poles=np.roots(a);outside=abs(zeros)>1
    reflected=zeros.copy();reflected[outside]=1/np.conj(zeros[outside])
    gain=active[0]*np.prod(abs(zeros[outside]))
    stable=bool(np.all(abs(poles)<1));boundary=bool(np.any(np.isclose(abs(zeros),1,rtol=1e-8,atol=1e-10)))
    strict=stable and not boundary
    minimum=Transfer(gain*np.atleast_1d(np.poly(reflected)),a,name='Fase mínima Hmin(z)' if strict else 'Factor de ceros interiores (no mínimo estricto)',sample_period_s=system.sample_period_s,roc={'mode':'right'})
    # Only exterior factors belong to the all-pass: do not introduce artificial
    # common zeros, especially 0/0 on the unit circle.
    ap_b=np.atleast_1d(np.poly(zeros[outside]))/np.prod(abs(zeros[outside]))
    ap_a=np.atleast_1d(np.poly(reflected[outside]))
    allpass=Transfer(np.r_[np.zeros(delay),ap_b],ap_a,name='Pasa todo A(z)',advance=system.advance,sample_period_s=system.sample_period_s,roc={'mode':'radius','radius':1.})
    lag=int(np.flatnonzero(allpass.b!=0)[0]);shift=lag-allpass.advance
    inverse=Transfer(np.r_[np.zeros(max(-shift,0)),allpass.a],allpass.b[lag:],name='Complemento Cmin(z) = 1/A(z)',advance=max(shift,0),sample_period_s=system.sample_period_s,roc={'mode':'radius','radius':1.})
    report='Fase mínima y pasa todo\n\nSe reflejan los ceros exteriores z₀ en 1/conj(z₀), se compensa la ganancia y se retira el desplazamiento temporal. Los polos se conservan.\n\n'+('El resultado es de fase mínima estricta bajo la interpretación causal de estos coeficientes.' if strict else 'No se afirma fase mínima estricta: hay polos no estables o ceros sobre/muy próximos al círculo unitario. Reflejar ceros no estabiliza polos ni elimina ceros del círculo.')
    return {'systems':[minimum,allpass,inverse],'signals':[],'report':report,'phase_adjustment':{'kind':'factor','strict':strict,'reflected':int(np.count_nonzero(outside)),'shift':delay-system.advance}}


def linear_phase(system):
    b,a=_input(system);m=len(b)-1;n=len(a)-1;delay=max(m-n,0)
    poles=np.roots(a)
    if np.any(np.isclose(abs(poles),1,rtol=1e-8,atol=1e-10)):
        raise ValueError('Hay polos sobre o muy próximos al círculo unitario. La construcción de fase lineal no tiene una respuesta en frecuencia finita; revisá esos polos antes de continuar.')
    # Hsharp(z)=conj(H(1/conj(z))). C=z^-D Hsharp and G=H*C.
    # Account for unequal polynomial degrees AND explicit input advances.
    lag=delay+n+system.advance-m
    complement=Transfer(np.r_[np.zeros(lag),np.conj(b[::-1])],np.conj(a[::-1]),name='Complemento lineal C(z)',sample_period_s=system.sample_period_s,roc={'mode':'radius','radius':1.})
    adjusted=Transfer(np.r_[np.zeros(delay+n-m),np.convolve(b,np.conj(b[::-1]))],np.convolve(a,np.conj(a[::-1])),name='Sistema de fase lineal G(z)',sample_period_s=system.sample_period_s,roc={'mode':'radius','radius':1.})
    iir=len(a)>1
    report='Construcción de fase lineal\n\nSe coloca en cascada una versión conjugada e invertida del original, con el retardo indicado. La identidad es algebraica; no es un ajuste por mínimos cuadrados.\n\nEl módulo resultante es el cuadrado del módulo original. La fase es −ωD y el retardo de grupo es D donde la respuesta no es cero.\n\n'+('El sistema es IIR: la ROC elegida incluye el círculo unitario y normalmente produce una realización bilateral no causal. Sus polos recíprocos no deben interpretarse como una realización causal estable. Ningún retardo finito convierte una cola anticausal infinita en causal.' if iir else 'El resultado es un FIR causal. Para una entrada con avance, el complemento añade el retardo necesario para compensarlo.')
    return {'systems':[adjusted,complement],'signals':[],'report':report,'phase_adjustment':{'kind':'linear','delay':delay,'iir':iir}}


def adjustment_summary(original,systems,selected,report,details):
    from .result_summary import Summary,Section,Formula,number
    from .phase_summary import transfer_formula
    linear=details['kind']=='linear';symbols=['G','C'] if linear else ['Hmin','A','Cmin']
    sections=[]
    def describe(title,value,symbol):
        formula,compact=transfer_formula(value,symbol)
        return Section(title,formulas=[formula],rows=[('b[k]',', '.join(number(v) for v in value.b)),('a[k]',', '.join(number(v) for v in value.a))] if compact else [])
    sections.append(describe('Sistema seleccionado · '+systems[selected].name,systems[selected],symbols[selected]))
    if linear:
        d=str(details['delay'])
        sections.append(Section('Qué agregar al original',paragraphs=['Conectá C en cascada con H. Aquí agregar significa multiplicar las transferencias; no sumar sus salidas. Se muestra el complemento numérico completo y el sistema G ya ajustado.'],formulas=[Formula('G(z)=H(z)*C(z)','G(z) = H(z) · C(z)'),Formula('C(z)=z^(-'+d+')*conjugate(H(1/conjugate(z)))','C(z) = z^(−'+d+') · conj(H(1/conj(z)))'),Formula('G(exp(i*w))=exp(-i*w*'+d+')*Abs(H(exp(i*w)))^2','G(e^(iω)) = exp(−iω·'+d+') · |H(e^(iω))|²')],rows=[('Retardo de grupo D',d+' muestras'),('Cambio de amplitud','|G| = |H|²; no se conserva el módulo original')]))
    else:
        sections.append(Section('Cómo obtener fase mínima',paragraphs=['Se sustituyen los ceros exteriores por sus recíprocos conjugados y se ajusta la ganancia para conservar el módulo. Se retira el retardo o avance explícito; los polos originales no cambian.', 'Para pasar de H a Hmin mediante cascada hay que quitar el factor pasa todo A: el complemento es Cmin=1/A. Esta inversa puede ser no causal o resultar inestable si se la fuerza a una realización causal; no se promete un compensador causal estable.'],formulas=[Formula('H(z)=Hmin(z)*A(z)','H(z) = Hmin(z) · A(z)'),Formula('Hmin(z)=H(z)*Cmin(z)','Hmin(z) = H(z) · Cmin(z)'),Formula('Cmin(z)=1/A(z)','Cmin(z) = 1/A(z)')],rows=[('Ceros reflejados',str(details['reflected'])),('Desplazamiento retirado',str(details['shift'])+' muestras (positivo = retardo)'),('Fase mínima estricta','Sí, con interpretación causal' if details['strict'] else 'No: consultar las condiciones del informe')]))
        sections.append(Section('Qué representa el pasa todo',paragraphs=['A contiene la fase y el desplazamiento que separan el original de Hmin. Su módulo es uno sobre el círculo unitario. Agregar A a Hmin reconstruye H; agregar otro pasa todo al original no lo convierte automáticamente en fase mínima. Los avances se conservan y su ROC incluye el círculo unitario.']))
    for index,value in enumerate(systems):
        if index!=selected:sections.append(describe('Resultado disponible · '+value.name,value,symbols[index]))
    sections.append(describe('Sistema original',original,'H'))
    sections.append(Section('Condiciones y lectura',paragraphs=[line for line in report.split('\n\n')[1:] if line.strip()]+['Cada sistema y complemento está disponible en Resultados para analizarlo, exportarlo o llevarlo a otra herramienta. La fase y el retardo no se definen en los ceros. Las identidades de frecuencia se refieren al círculo unitario; una ROC original incompatible no se modifica retroactivamente.', 'Los coeficientes son numéricos. La fórmula muestra hasta 12 cifras significativas; los datos reutilizados conservan la precisión almacenada.']))
    return Summary('Ajuste de fase · sistemas y complementos',sections)
