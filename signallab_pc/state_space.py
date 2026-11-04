"""Modelos de estado continuos/discretos, MIMO y simulación con entrada ZOH."""
from dataclasses import dataclass
import numpy as np
from scipy.signal import cont2discrete
from .filters import Transfer
from .resources import ensure_working_set
from .jobs import checkpoint

@dataclass
class StateModel:
    A: np.ndarray
    B: np.ndarray
    C: np.ndarray
    D: np.ndarray
    dt: float | None = None
    name: str = 'Sistema de estados'
    def __post_init__(self):
        for key in ('A','B','C','D'):
            value=np.asarray(getattr(self,key),dtype=np.complex128)
            if value.ndim!=2 or not np.isfinite(value).all():raise ValueError(f'{key} debe ser una matriz de números finitos.')
            setattr(self,key,value.copy())
        n=self.A.shape[0]
        if self.A.shape!=(n,n):raise ValueError('A debe ser cuadrada.')
        if self.B.shape[0]!=n or self.C.shape[1]!=n:raise ValueError('B y C deben ser compatibles con la cantidad de estados de A.')
        if self.B.shape[1]<1 or self.C.shape[0]<1 or self.D.shape!=(self.C.shape[0],self.B.shape[1]):raise ValueError('D debe tener una fila por salida y una columna por entrada.')
        if self.dt is not None:
            self.dt=float(self.dt)
            if not np.isfinite(self.dt) or self.dt<=0:raise ValueError('El periodo de muestreo debe ser positivo y finito.')
    @property
    def states(self):return self.A.shape[0]
    @property
    def inputs(self):return self.B.shape[1]
    @property
    def outputs(self):return self.C.shape[0]
    @property
    def domain(self):return 'analog' if self.dt is None else 'digital'
    def analysis(self):
        n=self.states;ensure_working_set(max(1,n*n*(self.inputs+self.outputs)),live_arrays=10)
        if n==0:return dict(states=0,inputs=self.inputs,outputs=self.outputs,poles=[],controllability_rank=0,observability_rank=0,stability='Sin estados dinámicos',rank_method='SVD con tolerancia numérica estándar')
        controllable=[];observable=[];ab=self.B.copy();ca=self.C.copy()
        for index in range(n):
            checkpoint();controllable.append(ab);observable.append(ca)
            if index<n-1:ab=self.A@ab;ca=ca@self.A
        ctr=np.hstack(controllable);obs=np.vstack(observable)
        if not np.isfinite(ctr).all() or not np.isfinite(obs).all():raise FloatingPointError('Las matrices de análisis exceden la precisión disponible; revisá la escala del modelo.')
        poles=np.linalg.eigvals(self.A);metric=poles.real if self.dt is None else abs(poles)-1
        tolerance=10*np.finfo(float).eps*max(1,np.linalg.norm(self.A,ord=2))*n
        stability='Internamente inestable' if np.any(metric>tolerance) else 'Internamente asintóticamente estable' if np.all(metric < -tolerance) else 'Sobre o cerca de la frontera; requiere análisis adicional'
        return dict(states=n,inputs=self.inputs,outputs=self.outputs,poles=[[float(z.real),float(z.imag)] for z in poles],
            controllability_rank=int(np.linalg.matrix_rank(ctr)),observability_rank=int(np.linalg.matrix_rank(obs)),stability=stability,
            rank_method='SVD con tolerancia max(shape)*sigma_max*eps; depende de escala y condicionamiento',stability_tolerance=float(tolerance),
            scope='Estabilidad interna del modelo; no se cancelan modos no controlables o no observables.')
    def response(self,omega,*,normalized=False):
        """Evaluate in rad/s, or in rad/muestra for a normalized digital grid."""
        from .state_frequency import response
        return response(self, omega, normalized=normalized)
    def discretize(self,dt,method='zoh'):
        if self.dt is not None:raise ValueError('El modelo ya es discreto.')
        dt=float(dt)
        if not np.isfinite(dt) or dt<=0:raise ValueError('El periodo debe ser positivo y finito.')
        if method not in ('zoh','bilinear','euler','backward_diff'):raise ValueError('Método de discretización no admitido.')
        ensure_working_set(max(1,(self.states+self.inputs)**2),live_arrays=16);checkpoint()
        if self.states==0:return StateModel(self.A,self.B,self.C,self.D,dt,self.name+' discreto')
        a,b,c,d,_=cont2discrete((self.A,self.B,self.C,self.D),dt,method=method);checkpoint()
        return StateModel(a,b,c,d,dt,self.name+' discreto')
    def to_transfer(self,input_index=0,output_index=0):
        if not 0<=input_index<self.inputs or not 0<=output_index<self.outputs:raise ValueError('Canal de entrada o salida fuera de rango.')
        ensure_working_set(max(1,self.states**2),live_arrays=12);checkpoint()
        if not self.states:return Transfer([self.D[output_index,input_index]],[1],self.domain,self.name,sample_period_s=self.dt,roc={'mode':'right'})
        from .state_frequency import _channel_models
        from .rational_frequency import complex_float

        channel = _channel_models(self,input_index,output_index)[0][0]
        channel.reduce()
        b = [complex_float(value) for value in channel.b]
        a = [complex_float(value) for value in channel.a]
        if self.dt is not None:
            # Descending powers of z become ascending powers of z⁻¹ after dividing by z^degree.
            b = [0j]*(len(a)-len(b))+b
        return Transfer(b,a,self.domain,f'{self.name}: y{output_index+1}/u{input_index+1}',
                        sample_period_s=self.dt,roc={'mode':'right'})
    @classmethod
    def from_transfer(cls,system,dt=None):
        from .realization import realize_system
        return realize_system(system).to_model(system.sample_period_s if dt is None else dt)
    def simulate(self,inputs,*,step=None,initial=None):
        values=np.asarray(inputs,dtype=np.complex128)
        if values.ndim==1 and self.inputs==1:values=values[:,None]
        if values.ndim!=2 or values.shape[1]!=self.inputs or not values.shape[0] or not np.isfinite(values).all():raise ValueError('La entrada debe tener una columna por canal y valores finitos.')
        step=self.dt if step is None else float(step)
        if step is None or not np.isfinite(step) or step<=0:raise ValueError('Indicá un paso temporal positivo para la simulación continua.')
        if self.dt is not None and not np.isclose(step,self.dt,rtol=1e-12,atol=0):raise ValueError('El paso debe coincidir con el periodo del modelo discreto.')
        n=self.states;count=values.shape[0]
        ensure_working_set(max(1,count*(n+self.inputs+self.outputs)),live_arrays=6)
        state=np.zeros(n,dtype=complex) if initial is None else np.asarray(initial,dtype=complex)
        if state.shape!=(n,) or not np.isfinite(state).all():raise ValueError('Indicá un estado inicial finito por cada estado del modelo.')
        model=self.discretize(step,'zoh') if self.dt is None else self
        states=np.empty((count,n),dtype=complex);output=np.empty((count,self.outputs),dtype=complex)
        with np.errstate(over='ignore',invalid='ignore'):
            for k in range(count):
                if k%256==0:checkpoint(k/count)
                states[k]=state;output[k]=self.C@state+self.D@values[k]
                if k<count-1:state=model.A@state+model.B@values[k]
        if not np.isfinite(states).all() or not np.isfinite(output).all():raise FloatingPointError('La simulación excedió el rango numérico; no se guardó una salida parcial.')
        time=np.arange(count)*step
        if not np.isfinite(time).all() or (count>1 and np.any(np.diff(time)<=0)):raise ValueError('El reloj excede la precisión disponible.')
        checkpoint(1);return time,output,states
