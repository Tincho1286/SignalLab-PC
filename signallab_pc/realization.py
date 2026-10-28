"""Causal direct-form II/integrator realizations; preserve supplied SOS stages."""
from dataclasses import dataclass
import numpy as np
from .filters import Transfer
from .resources import ensure_working_set
from .jobs import checkpoint


@dataclass(frozen=True)
class Stage:
    b: np.ndarray
    a: np.ndarray
    @property
    def order(self):return len(self.a)-1


@dataclass(frozen=True)
class Realization:
    stages: tuple
    domain: str
    name: str
    cascade: bool=False
    @property
    def states(self):return sum(stage.order for stage in self.stages)

    def to_model(self,dt=None):
        from .state_space import StateModel
        if self.domain=='digital':
            if dt is None or not np.isfinite(dt) or dt<=0:raise ValueError('Indicá un período T positivo y finito para el modelo discreto.')
        elif dt is not None:raise ValueError('El sistema continuo no lleva período discreto.')
        n=self.states;ensure_working_set(max(1,n*n),live_arrays=16)
        A=np.empty((0,0),complex);B=np.empty((0,1),complex);C=np.empty((1,0),complex);D=np.ones((1,1),complex)
        for stage in self.stages:
            checkpoint();size=stage.order
            a=np.zeros((size,size),complex);b=np.zeros((size,1),complex)
            if size:
                a[0]=-stage.a[1:];a[1:,:-1]=np.eye(size-1);b[0,0]=1
            c=(stage.b[1:]-stage.b[0]*stage.a[1:]).reshape(1,size);d=np.array([[stage.b[0]]])
            # Downstream section is driven by the upstream output, including D.
            previous=A.shape[0];joined=np.zeros((previous+size,previous+size),complex)
            joined[:previous,:previous]=A;joined[previous:,:previous]=b@C;joined[previous:,previous:]=a
            B=np.vstack((B,b@D));C=np.hstack((d@C,c));D=d@D;A=joined
        return StateModel(A,B,C,D,dt,self.name+' · realización')


def _stage(system):
    b=system.b.copy();a=system.a.copy()
    if system.domain=='digital':
        b=np.trim_zeros(b,'b') if np.any(b) else np.array([0j]);a=np.trim_zeros(a,'b')
        length=max(len(a),len(b));b=np.pad(b,(0,length-len(b)));a=np.pad(a,(0,length-len(a)))
    else:
        b=np.trim_zeros(b,'f') if np.any(b) else np.array([0j])
        if len(b)>len(a):raise ValueError('H(s) es impropia: necesita derivadores. Este diagrama utiliza integradores y requiere grado del numerador ≤ grado del denominador. No se descartan los términos impropios.')
        b=np.pad(b,(len(a)-len(b),0))
    b.setflags(write=False);a.setflags(write=False)
    return Stage(b,a)


def realize_system(system,advance=0):
    if advance or system.advance:raise ValueError('H(z) contiene un avance temporal. Una cadena causal de retardos no realiza esa fórmula completa; no se reemplaza el avance por un retardo.')
    ensure_working_set(max(len(system.b),len(system.a)),live_arrays=8)
    cascade=system.sos is not None
    stages=tuple(_stage(Transfer(row[:3],row[3:],'digital')) for row in system.sos) if cascade else (_stage(system),)
    return Realization(stages,system.domain,system.name,cascade)


def realization_summary(value):
    from .result_summary import Summary,Section,Formula,number
    digital=value.domain=='digital';sections=[Section('Estructura',rows=[('Dominio','Discreto' if digital else 'Continuo'),('Forma','Cascada de secciones · directa II' if value.cascade else 'Directa II · cadena de retardos' if digital else 'Cadena de integradores'),('Estados',value.states)],paragraphs=[
        'Los bloques azules multiplican por b[k]; los ámbar por −a[k]. Los círculos suman sus entradas. Cada bloque verde guarda una muestra anterior.' if digital else 'Los bloques azules multiplican por b[k]; los ámbar por −a[k]. Los círculos suman sus entradas. Cada bloque verde integra su entrada.',
        'Los sumadores de cada columna acumulan hacia arriba. Los coeficientes ya están divididos por a[0].'])]
    if value.cascade:sections.append(Section('Conexión de las secciones',paragraphs=['La salida de cada sección alimenta la entrada de la siguiente, en el orden de la cascada conservada. Cada sección tiene su propia variable v y sus propios estados q. No se desarrolla un único polinomio para construir estas matrices.']))
    for index,stage in enumerate(value.stages,1):
        n=stage.order
        equations=([Formula('v = u - Sum(a[k]*q[k],(k,1,'+str(n)+'))','v = u − Σ desde k=1 hasta '+str(n)+' de a[k]·q[k]'),Formula('y = b[0]*v + Sum(b[k]*q[k],(k,1,'+str(n)+'))','y = b[0]·v + Σ desde k=1 hasta '+str(n)+' de b[k]·q[k]')] if n else [Formula('y = ('+number(stage.b[0]).replace('i','*i')+')*u','y = ('+number(stage.b[0])+')·u')])
        paragraphs=[]
        if n:
            paragraphs=['q₁[n+1] = v[n]; qₖ[n+1] = qₖ₋₁[n] para k=2…'+str(n)+'. Las salidas qₖ[n] de los retardos son los estados.' if digital else 'dq₁/dt = v(t); dqₖ/dt = qₖ₋₁(t) para k=2…'+str(n)+'. Las salidas qₖ(t) de los integradores son los estados.']
            if n==1:paragraphs=['q₁[n+1] = v[n]. La salida del retardo es el estado q₁[n].' if digital else 'dq₁/dt = v(t). La salida del integrador es el estado q₁(t).']
        sections.append(Section('Sección '+str(index) if value.cascade else 'Ecuaciones de la realización',paragraphs=paragraphs,formulas=equations))
        sections.append(Section('Coeficientes · sección '+str(index) if value.cascade else 'Coeficientes del diagrama',rows=[('k='+str(k),'a[k] = '+number(a)+'; b[k] = '+number(b)) for k,(a,b) in enumerate(zip(stage.a,stage.b))]))
    sections.append(Section('Condiciones e interpretación',paragraphs=[
        'La transferencia relaciona entrada y salida con estados iniciales nulos. Al enviar las matrices a Espacio de estados podés estudiar otros estados iniciales. Los q de esta realización no son, en general, las derivadas ni las muestras anteriores de y.',
        'No se cancelan polos y ceros ni se garantiza una realización mínima. H=0 o una cancelación externa pueden ocultar modos internos. Se eliminan solamente coeficientes extremos exactamente nulos que no aportan dinámica; los coeficientes pequeños no se recortan.',
        'Las matrices usan el orden de estados q₁,…,qN; en una cascada, sección por sección. Se usa precisión compleja de 64 bits por componente. Una forma directa de orden alto puede estar mal condicionada; las secciones SOS recibidas se conservan.',
        'En discreto, T sólo establece el reloj físico al enviar el modelo de estados: no cambia los coeficientes, el número de retardos ni H(z).' if digital else 'El diagrama realiza transferencias racionales propias. No convierte filtros ideales definidos por bandas en sistemas finitos exactos.']))
    return Summary('Realización del sistema',sections)
