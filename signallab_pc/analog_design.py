"""Diseño analógico por tolerancias de amplitud y bordes angulares."""
import numpy as np
from scipy import signal as sp
from .filters import Transfer
from .resources import ensure_working_set
from .jobs import checkpoint

FAMILIES={'butter':'Butterworth','cheby1':'Chebyshev I','cheby2':'Chebyshev II','ellip':'Elíptico'}

def design(wp,ws,dp,ds,method):
    wp=np.asarray(wp,float);ws=np.asarray(ws,float)
    if wp.ndim!=1 or wp.shape!=ws.shape or wp.size not in (1,2) or not np.all(np.isfinite(np.r_[wp,ws])) or np.any(np.r_[wp,ws]<=0):raise ValueError('Usá uno o dos bordes por banda, positivos y finitos en rad/s.')
    if wp.size==1 and wp[0]!=ws[0]:kind='lowpass' if wp[0]<ws[0] else 'highpass'
    elif wp.size==2 and ws[0]<wp[0]<wp[1]<ws[1]:kind='bandpass'
    elif wp.size==2 and wp[0]<ws[0]<ws[1]<wp[1]:kind='bandstop'
    else:raise ValueError('Las bandas deben estar ordenadas y separadas por transiciones positivas.')
    if not 0<dp<1 or not 0<ds<1-dp:raise ValueError('Usá 0 < δp < 1 y 0 < δs < 1−δp.')
    methods=list(FAMILIES) if method=='compare' else [method]
    if any(m not in FAMILIES for m in methods):raise ValueError('Familia de filtro no admitida.')
    gpass=-20*np.log10(1-dp);gstop=-20*np.log10(ds);edges=np.r_[wp,ws];lo=float(edges.min()/100);hi=float(edges.max()*100)
    if lo<=0 or not np.isfinite(hi):raise ValueError('Los bordes exceden el rango numérico del diseño.')
    w=np.unique(np.r_[0,np.geomspace(lo,hi,32769),edges]);systems=[];reports=[]
    orders={'butter':sp.buttord,'cheby1':sp.cheb1ord,'cheby2':sp.cheb2ord,'ellip':sp.ellipord}
    for index,family in enumerate(methods):
        checkpoint(index/len(methods));order,critical=orders[family](wp,ws,gpass,gstop,analog=True)
        final_order=int(order)*(2 if wp.size==2 else 1);ensure_working_set(final_order**2+len(w),live_arrays=10)
        kwargs=dict(N=int(order),Wn=critical,btype=kind,analog=True,output='zpk')
        if family in ('cheby1','ellip'):kwargs['rp']=gpass
        if family in ('cheby2','ellip'):kwargs['rs']=gstop
        z,p,k=getattr(sp,family if family!='ellip' else 'ellip')(**kwargs)
        b,a=sp.zpk2tf(z,p,k);system=Transfer(b,a,'analog',FAMILIES[family]+' analógico');systems.append(system)
        _,reference=sp.freqs_zpk(z,p,k,worN=w);response=system.response(w)
        if not np.all(np.isfinite(response)) or not np.all(np.isfinite(reference)):raise ValueError('Respuesta no finita: revisá escala de frecuencias, orden y tolerancias.')
        disagreement=float(np.max(abs(response-reference)/np.maximum(1,abs(reference))))
        if disagreement>1e-5:raise ValueError('Los coeficientes expandidos pierden precisión para este diseño. Relajá tolerancias o escala; no se publica una transferencia inconsistente.')
        h=abs(response)
        if kind=='lowpass':passing=w<=wp[0];stopping=w>=ws[0]
        elif kind=='highpass':passing=w>=wp[0];stopping=w<=ws[0]
        elif kind=='bandpass':passing=(w>=wp[0])&(w<=wp[1]);stopping=(w<=ws[0])|(w>=ws[1])
        else:passing=(w<=wp[0])|(w>=wp[1]);stopping=(w>=ws[0])&(w<=ws[1])
        minimum=float(h[passing].min());maximum=float(h[passing].max());rejection=float(h[stopping].max());excess=max(1-dp-minimum,maximum-1,rejection-ds)
        reports.append(f'{FAMILIES[family]}\nOrden del prototipo: {order}\nOrden final: {final_order}\nMódulo en paso: {minimum:.9g} a {maximum:.9g}\nMáximo en rechazo: {rejection:.9g}\nComprobación en rejilla: '+('cumple dentro del redondeo numérico.' if excess<=1e-8 else 'revisar desviación de tolerancias.')+f'\nDiferencia de representación: {disagreement:.3g}')
    report='Diseño analógico por especificaciones\n\nFrecuencias en rad/s; sin límite de Nyquist.\n'+f'Paso permitido: [{1-dp:g}, 1]\nRechazo máximo: {ds:g}\nPérdida de paso: {gpass:.9g} dB\nAtenuación de rechazo: {gstop:.9g} dB\n\n'+'\n\n'.join(reports)+'\n\nOrden seleccionado dentro de cada familia. La comprobación usa 32769 puntos logarítmicos, los bordes y cero; no certifica máximos continuos ni representa una realización física con componentes. Los coeficientes de H(s) se pueden exportar, convertir a digital o usar en respuesta temporal.'
    return {'report':report,'signals':[],'systems':systems,'comparison':len(systems)>1,'specifications':{'domain':'analog','kind':kind,'wp':wp.tolist(),'ws':ws.tolist(),'dp':dp,'ds':ds,'pass_upper':1,'plot_range':[float(edges.min()/10),float(edges.max()*10)]}}
