"""Develop real plotted components without opaque re/im/abs/arg placeholders."""
import sympy as sp
from .result_summary import Section,Formula


def angle(real,imag,positive=False):
    if positive or real.is_positive:return sp.atan(imag/real)
    # atan alone loses the quadrant. Zero is deliberately undefined.
    return sp.Piecewise((sp.atan(imag/real),real>0),
        (sp.atan(imag/real)+sp.pi,sp.And(real<0,imag>=0)),
        (sp.atan(imag/real)-sp.pi,sp.And(real<0,imag<0)),
        (sp.pi/2,sp.And(sp.Eq(real,0),imag>0)),
        (-sp.pi/2,sp.And(sp.Eq(real,0),imag<0)))


def _coefficient(value):
    z=complex(value)
    scalar=lambda v:sp.Integer(int(v)) if v==int(v) else sp.Float(repr(v),17)
    return scalar(z.real),scalar(z.imag)


def polynomial(values,w,digital):
    real=[];imag=[]
    for k,value in enumerate(values):
        a,b=_coefficient(value)
        if digital:
            real.append(a*sp.cos(k*w)+b*sp.sin(k*w));imag.append(b*sp.cos(k*w)-a*sp.sin(k*w))
        else:
            power=len(values)-1-k;factor=sp.I**(power%4);c=(a+sp.I*b)*factor
            real.append(sp.re(c)*w**power);imag.append(sp.im(c)*w**power)
    return sp.Add(*real),sp.Add(*imag)


def transfer_components(system,advance=0,*,derivative=False):
    from .transfer_plane import effective_plane_system,causal_sections
    system=effective_plane_system(system)
    w=sp.Symbol('w',real=True);digital=system.domain=='digital'
    # Keep SOS factored; expanding their polynomials defeats the stored model.
    stages=causal_sections(system) if system.sos is not None else [None]
    r=sp.S.One;i=sp.S.Zero;norm=sp.S.One;definitions=[];delays=[]
    for index,row in enumerate(stages,1):
        b,a=(row[:3],row[3:]) if system.sos is not None else (system.b,system.a)
        br,bi=polynomial(b,w,digital);ar,ai=polynomial(a,w,digital)
        rr=br*ar+bi*ai;ii=bi*ar-br*ai;den=ar**2+ai**2
        sr,si=rr/den,ii/den
        if derivative:delays.append(-(br*sp.diff(bi,w)-bi*sp.diff(br,w))/(br**2+bi**2)+(ar*sp.diff(ai,w)-ai*sp.diff(ar,w))/(ar**2+ai**2))
        r,i=r*sr-i*si,r*si+i*sr
        if len(stages)>2:
            rrname=sp.Symbol('R'+str(index),real=True);iiname=sp.Symbol('I'+str(index),real=True)
            definitions.extend([(rrname,r),(iiname,i)]);r,i=rrname,iiname
        norm*= (br**2+bi**2)/den
    shift=int(system.advance)+int(advance)
    if shift:r,i=r*sp.cos(shift*w)-i*sp.sin(shift*w),r*sp.sin(shift*w)+i*sp.cos(shift*w)
    extra=dict(definitions=definitions)
    if len(stages)==1 and not shift:extra.update(angle_real=rr,angle_imag=ii)
    if derivative:extra['delay']=sp.Add(*delays)-shift
    return w,r,i,sp.sqrt(norm),extra


def expression_components(source,variable):
    from .symbolic import parse
    value=parse(source);coordinate={'n':sp.Symbol('n',integer=True),'t':sp.Symbol('t',real=True),'w':sp.Symbol('w',real=True)}[variable]
    if len(str(value))>1800 or sp.count_ops(value)>140:raise ValueError('Expresión extensa: se conserva la definición original.')
    if any(v.is_real is not True for v in value.free_symbols):raise ValueError('El desarrollo requiere conocer si los parámetros son reales o complejos.')
    # Piecewise values are developed separately; its conditions stay intact.
    if isinstance(value,sp.Piecewise):
        pairs=[(part.as_real_imag(),condition) for part,condition in value.args]
        r=sp.Piecewise(*[(pair[0],condition) for pair,condition in pairs]);i=sp.Piecewise(*[(pair[1],condition) for pair,condition in pairs])
    else:r,i=value.as_real_imag()
    if (r.has(sp.re,sp.im,sp.arg) or i.has(sp.re,sp.im,sp.arg)):raise ValueError('No se pudo desarrollar esta componente; la definición original permanece disponible.')
    return coordinate,r,i,sp.sqrt(r**2+i**2)


def sections(parts,role,*,discrete=False,continuous_phase=False):
    w,r,i,magnitude=parts[:4];extra=parts[4] if len(parts)>4 else {};variable=str(w);suffix='['+variable+']' if discrete else '('+variable+')'
    real_name='R'+suffix;imag_name='I'+suffix
    formulas=[Formula(str(symbol)+' = '+sp.sstr(value),str(symbol)+' = '+sp.sstr(value),numeric=True) for symbol,value in extra.get('definitions',[])];notes=[]
    if formulas:notes.append('Se conserva la cascada: cada par Rj, Ij es la parte real e imaginaria acumulada hasta esa sección. Todas las secciones se desarrollan con sus coeficientes almacenados.')
    # Inline compact answers. Long answers use fully defined real components.
    short=sum(len(str(v)) for v in (r,i))<650
    rr,ii=(r,i) if short else (sp.Symbol('R',real=True),sp.Symbol('I',real=True))
    if role in ('real','imag'):value=r if role=='real' else i;left='y'+suffix
    elif role in ('magnitude','db','magnitude_db'):
        value=magnitude
        if not short:value=sp.sqrt(rr**2+ii**2)
        if role in ('db','magnitude_db'):value=20*sp.log(value)/sp.log(10)
        left='M'+suffix
    elif role in ('phase','phase_unwrapped'):
        value=angle(extra.get('angle_real',rr),extra.get('angle_imag',ii));left='phi'+suffix
        notes.append('Ángulo principal en radianes. La expresión usa arctangente y distingue los cuadrantes; en R = I = 0 la fase no está definida.')
        if continuous_phase or role=='phase_unwrapped':notes.append('La figura desenrolla este ángulo: suma o resta múltiplos de 2π para evitar saltos entre puntos consecutivos de cada tramo. La fórmula anterior es la fase principal; la rama continua depende del intervalo y del recorrido de la rejilla.')
    elif role=='delay':
        value=extra['delay'] if 'delay' in extra else -(r*sp.diff(i,w)-i*sp.diff(r,w))/(r**2+i**2);left='tau'+suffix
        if sp.count_ops(value)>240 and 'delay' not in extra:
            value=-(rr*sp.Symbol('Ip',real=True)-ii*sp.Symbol('Rp',real=True))/(rr**2+ii**2)
            short=False;notes.append('Rp e Ip son las derivadas respecto del eje de las componentes desarrolladas R e I. El retardo no se define en ceros ni en polos.')
    elif role=='density_db':
        value=10*sp.log(r)/sp.log(10);left='D'+suffix;notes.append('Esta escala requiere una densidad real estrictamente positiva.')
    else:return []
    source=sp.sstr(value)
    if value is sp.nan:return [Section('Componente no definida',paragraphs=notes+['La definición no determina un valor de esta componente. En particular, una señal idénticamente nula no tiene fase ni retardo de grupo.'])]
    if not short:
        formulas.extend([Formula(real_name+' = '+sp.sstr(r),real_name+' = '+sp.sstr(r),numeric=True),Formula(imag_name+' = '+sp.sstr(i),imag_name+' = '+sp.sstr(i),numeric=True)])
        if value.has(sp.Symbol('Rp',real=True)):
            formulas.extend([Formula('Rp = '+sp.sstr(sp.diff(r,w)),'Rp = '+sp.sstr(sp.diff(r,w)),numeric=True),Formula('Ip = '+sp.sstr(sp.diff(i,w)),'Ip = '+sp.sstr(sp.diff(i,w)),numeric=True)])
        notes.append('En la fórmula final, R e I son las componentes numéricas desarrolladas arriba, evaluadas en la misma coordenada.')
    formulas.append(Formula(left+' = '+source,left+' = '+source,numeric=True))
    notes.append('El desarrollo utiliza los coeficientes almacenados y las mismas cancelaciones exactas del modelo, sin aproximar raíces cercanas. Se conservan las condiciones y exclusiones registradas; una cancelación algebraica no elige una ROC ni define la fase en un cero.')
    return [Section('Fórmula de la curva seleccionada',formulas=formulas,paragraphs=notes)]
