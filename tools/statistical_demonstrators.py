"""Run the five reproducible Phase 05 studies through the application engines."""

import argparse
from hashlib import file_digest
import math
from pathlib import Path
import sys
from threading import Event

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from signallab_pc import session
from signallab_pc.adaptive_filter import compare_adaptive
from signallab_pc.ar_estimation import fit as fit_ar
from signallab_pc.atomic_file import write_json
from signallab_pc.communications_channel import AWGNSpec, add_awgn
from signallab_pc.communications_fading import FadingPath, FadingSpec, apply_fading
from signallab_pc.communications_impairments import PhaseNoiseSpec, apply_phase_noise
from signallab_pc.descriptive_statistics import describe_record
from signallab_pc.dsp_application import PSDRequest, estimate_psd, store_signal
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.kalman_filter import kalman_filter
from signallab_pc.model import Signal
from signallab_pc.monte_carlo import CampaignSpec, Scenario, campaign_trajectory, load_campaign, run_campaign, store_campaign
from signallab_pc.operation_provenance import content_digest
from signallab_pc.probability import Distribution, generate_realizations, population
from signallab_pc.project import Project
from signallab_pc.random_models import analyze, realization
from signallab_pc.state_space import StateModel
from signallab_pc.statistical_inference import fit_distribution
from signallab_pc.statistics_results import store_statistics
from signallab_pc.stochastic_covariance import estimate_correlation
from signallab_pc.time_series_identification import arma_diagnostics, arma_forecast, fit_arma, partial_autocorrelation
from signallab_pc.wiener_filter import wiener_fir, wiener_hopf


def check(label, value, expected, atol):
    value, expected = float(value), float(expected)
    if not math.isfinite(value) or abs(value-expected) > atol:
        raise AssertionError(f'{label}: valor {value}, esperado {expected} ± {atol}')
    return {'quantity':label,'actual':value,'reference':expected,'absolute_tolerance':atol}


def distributions(_):
    results, checks = [], []
    replicas, level = 64, .95
    for family, parameters, parameter, moments in (
        ('normal', {'mean':1.,'std':2.}, 'mean', (1.,4.)),
        ('exponential', {'scale':2.}, 'scale', (2.,4.)),
    ):
        model = Distribution(family, parameters)
        expected_mean, expected_variance = moments
        stats = population(model)
        checks.append(check(family+' media poblacional', stats['mean']['value'], expected_mean, 1e-13))
        for size in (64, 512):
            seed = 2026113000+size+(family=='exponential')
            estimates, covered = [], 0
            for source in generate_realizations(model,size,seed,replicas=replicas):
                observed = describe_record(source)
                fit = fit_distribution(source,family,level=level,iid=True)
                estimate = fit['estimated_distribution']['parameters'][parameter]
                checks.append(check(family+' estimación frente a media directa', estimate, observed['mean']['value'], 2e-12))
                estimates.append(estimate)
                low, high = (item['value'] for item in fit['confidence_intervals']['parameters'][parameter])
                covered += low <= parameters[parameter] <= high
            bound = 6*math.sqrt(expected_variance/(size*replicas))
            checks.append(check(f'{family} media de réplicas, N={size}', np.mean(estimates), expected_mean, bound))
            coverage_tolerance = 6*math.sqrt(level*(1-level)/replicas)+1/replicas
            checks.append(check(f'{family} cobertura, N={size}', covered/replicas, level, coverage_tolerance))
            results.append({'family':family,'seed':seed,'samples':size,'replicas':replicas,
                            'parameter':parameter,'estimates':estimates,'intervals_covering_true_parameter':covered})
    return {'study':'Distribuciones e inferencia','designs':results,'checks':checks}


def identification(_):
    rate, n, reserve = 128, 4096, 256
    rows, checks = [], []
    for index,(phi,theta) in enumerate(((.6,0.),(0.,.4),(.6,.4))):
        a, b = ([1.,-phi] if phi else [1.]), ([1.,theta] if theta else [1.])
        model=analyze(b,a,noise_std=1.,max_lag=20)
        model.system.sample_period_s=1/rate
        source=realization(model,n,2026113010+index,origin=-12)
        acf=estimate_correlation(source,max_lag=12,remove_mean=True)
        pacf=partial_autocorrelation(acf.values[12:].real)
        spectrum=estimate_psd(PSDRequest(source,method='bartlett',segment=256,overlap=0,window='boxcar'))
        fit=fit_arma(source,int(bool(phi)),int(bool(theta)),validation=reserve)
        residual=arma_diagnostics(source,fit,max_lag=16)
        forecast=arma_forecast(source,fit,8)
        variance=1.+(phi+theta)**2/(1-phi**2)
        correlation_one=(phi*(variance-1)+phi+theta)/variance
        prefix=f'ARMA({fit["p"]},{fit["q"]})'
        checks.extend([
            check(prefix+' varianza teórica',model.variance,variance,1e-12),
            check(prefix+' ACF retardo uno',acf.values[13].real/acf.values[12].real,correlation_one,.08),
            check(prefix+' PACF retardo uno',pacf[1],correlation_one,.08),
            check(prefix+' Parseval PSD discreta',np.sum(spectrum.values.real)*spectrum.step,np.mean(abs(source.values)**2),1e-12),
        ])
        found = (-fit['a'][1] if phi else 0.,fit['b'][1] if theta else 0.)
        checks.extend(check(prefix+' '+label,estimate,truth,.14) for label,estimate,truth in
                      zip(('phi','theta'),found,(phi,theta),strict=True))
        if not fit['identifiable'] or forecast['signals'][0].origin!=source.origin+n:
            raise AssertionError(prefix+' no identificable o pronóstico fuera de reloj.')
        methods={}
        if phi and not theta:
            for name in ('ols','yw','burg'):
                methods[name]=-fit_ar(source,1,method=name,validation=reserve)['a'][1]
                checks.append(check(name+' coeficiente AR(1)',methods[name],phi,.08))
        rows.append({'seed':2026113010+index,'a':a,'b':b,'estimate':list(found),
                     'methods_on_ar_case':methods,'first_forecast':float(forecast['signals'][0].values[0].real),
                     'residual_ljung_box':residual['rows'][-1],'validation_mse':fit['validation_mse']})
    return {'study':'Identificación y pronóstico','models':rows,'checks':checks}


def filtering(_):
    seed, n, reserve = 2026113020, 640, 128
    clean = Signal(np.resize([-1.,1.,1.,-1.],n), metadata={'sample_rate_hz':64}, name='Referencia')
    measured=add_awgn(clean,AWGNSpec('snr',6.,seed,'real')).signal
    noise_power=10**(-.6)
    ideal=1/(1+noise_power)
    theoretical=wiener_hopf([1+noise_power],[1.],1.)
    measured_fit=wiener_fir(measured,clean,1,reserve=reserve)
    reference_mse=float(np.mean(abs(measured.values[-reserve:]-clean.values[-reserve:])**2))
    empirical=measured_fit[0]['validation_mse']['value']
    if empirical>=reference_mse:
        raise AssertionError('Wiener debe reducir el MSE en la reserva del ejemplo.')
    model=StateModel([[1.]],[[0.]],[[1.]],[[0.]],1/64)
    observation=add_awgn(Signal(np.full(64,2.)),AWGNSpec('snr',6.,seed+1,'real',signal_power=1.)).signal
    kalman=kalman_filter(model,observation.values.real[:,None],[[0.]],[[noise_power]],[0.],[[1.]])
    direct=float(np.sum(observation.values.real)/(len(observation.values)+noise_power))
    drive=Signal(np.resize([1.,-1.,.5,-.5],n))
    desired=Signal(1.5*drive.values)
    variants=compare_adaptive(drive,desired,[{'method':'lms','step':.12},{'method':'nlms','step':.5},
                                            {'method':'rls','forgetting':1.,'ridge':1.}],length=1,reserve=reserve)
    checks=[
        check('Wiener ganancia teórica',theoretical['coefficients']['real'][0],ideal,1e-12),
        check('Wiener MSE teórico',theoretical['theoretical_mse']['value'],1-ideal,1e-12),
        check('Wiener FIR aprendido',measured_fit[1].b[0].real,ideal,.08),
        check('Kalman frente al posterior por lote',kalman.corrected[-1,0].real,direct,1e-12),
        check('Kalman varianza posterior',kalman.posterior_covariance[-1,0,0].real,
              noise_power/(len(observation.values)+noise_power),1e-12),
    ]
    learning=[]
    for variant in variants:
        error=variant.error.values
        label=variant.report['method']
        first, last=(float(np.mean(abs(values)**2)) for values in (error[:32],error[-reserve:]))
        if not last<first:
            raise AssertionError(label+' no redujo el error de la reserva.')
        checks.append(check(label+' peso identificado',variant.system.b[0].real,1.5,.02))
        learning.append({'method':label,'first_mse':first,'reserved_mse':last})
    return {'study':'Wiener, Kalman y adaptación','seed':seed,'noise_power':noise_power,
            'wiener_reserved_mse':empirical,'unfiltered_reserved_mse':reference_mse,'learning':learning,'checks':checks}


def monte_carlo(folder):
    spec=CampaignSpec(tuple(Scenario(f'p={p}',Distribution('bernoulli',{'p':p})) for p in (.01,.06,.15)),
                      'probability',2026113030,samples=128,replicas=64,batch=8,
                      low=1,high=1,common_random_numbers=True,confidence=.999)
    interrupted=folder/'campaña'
    stop=Event()

    def progress(percent):
        if percent>=50:
            stop.set()

    try:
        run_campaign(spec,interrupted,ExecutionContext(cancel=stop,progress=progress))
    except OperationCancelled:
        pass
    else:
        raise AssertionError('La campaña no se interrumpió.')
    if len(load_campaign(interrupted).replicas)!=32:
        raise AssertionError('La campaña no conservó 32 réplicas completas.')
    resumed=run_campaign(spec,interrupted)
    fresh=run_campaign(spec,folder/'referencia')
    if resumed.replicas!=fresh.replicas:
        raise AssertionError('Las réplicas cambiaron al reanudar la campaña.')
    checks=[]
    for row,p in zip(resumed.report['summaries'],(.01,.06,.15),strict=True):
        trials=row['trials']
        if not row['interval'][0]<=p<=row['interval'][1]:
            raise AssertionError('Intervalo binomial fuera de la referencia prefijada.')
        checks.append(check('Probabilidad '+row['scenario'],row['value'],p,6*math.sqrt(p*(1-p)/trials)))
    counts,curves=campaign_trajectory(resumed)
    project=Project()
    key=store_campaign(project,resumed)
    path=folder/'monte-carlo.slproj'
    session.save(path,project,session.empty_workspace())
    reloaded,_=session.load(path)
    if reloaded.get(key)['replicate_summaries']!=[list(values) for values in resumed.replicas]:
        raise AssertionError('El proyecto alteró los recuentos de Monte Carlo.')
    return {'study':'Monte Carlo con números comunes','same_replicas_on_resume':True,
            'summary':resumed.report,'convergence':{'replicas':counts.tolist(),'estimates':curves.tolist()},
            'checks':checks}


def channels(folder):
    rate, n, replicas, doppler = 128, 1024, 24, 12
    source=Signal(np.ones(n),origin=-16,metadata={'sample_rate_hz':rate,'time_start_s':0.})
    project=Project()
    parent=project.add(source,operation='Entrada de prueba del canal')
    checks,studies=[],[]
    for index,(name,k,fd) in enumerate((('Rayleigh',0.,None),('Rician',3.,None),('Clarke',0.,doppler))):
        results=[]
        for replica in range(replicas):
            seed=2026113040+100*index+replica
            fading=apply_fading(source,FadingSpec((FadingPath(0,1.,k),),seed,fd))
            path=fading.realizations[0].coefficients
            law=Distribution('rayleigh',{'scale':math.sqrt(.5)}) if not k else Distribution(
                'rician',{'ratio':math.sqrt(2*k),'scale':math.sqrt(.5/(1+k))})
            descriptive=describe_record(path,'magnitude',diagnostics=True,reference=law,qq_points=33)
            correlation=estimate_correlation(path,max_lag=8)
            spectrum=estimate_psd(PSDRequest(path,method='welch',segment=256,overlap=128))
            checks.append(check(name+' potencia módulo de la réplica',descriptive['rms']['value']**2,
                                correlation.values[8].real,2e-12))
            outside=abs(spectrum.axis)>doppler+2*spectrum.step
            results.append((correlation.values[8].real,correlation.values[10].real,
                            np.sum(spectrum.values.real)*spectrum.step,
                            np.sum(spectrum.values.real[outside])*spectrum.step,np.mean(abs(path.values) <= 1)))
            if replica==0:
                output=store_signal(project,fading.signal,parents=(parent,))
                coefficients=project.add(path,operation='Realización del coeficiente',parents=(output,))
                store_statistics(project,descriptive,[(path,coefficients,())],'Distribución de la envolvente')
                store_signal(project,spectrum,parents=(coefficients,))
        power,lag_two,spectral_power,leakage,cdf=np.mean(results,axis=0)
        tolerance=.15 if fd else .06
        checks.extend([check(name+' potencia media',power,1.,tolerance),
                       check(name+' potencia por PSD',spectral_power,power,tolerance)])
        if fd:
            angle=2*math.pi*np.arange(2048)/2048
            expected=np.mean(np.cos(2*math.pi*doppler*2/rate*np.cos(angle)))
            checks.append(check('Clarke ACF retardo dos',lag_two,expected,.15))
            checks.append(check('Clarke fuga a más de dos bins del borde',leakage,0.,.06))
        else:
            checks.append(check(name+' ACF retardo dos',lag_two,k/(1+k),.06))
        # At |h|=1 the Rice power CDF is a Poisson mixture of integer-shape
        # gamma CDFs. The k=0 expression reduces to the Rayleigh CDF.
        x=1+k
        reference_cdf=sum(math.exp(-k)*k**j/math.factorial(j) *
                          (1-math.exp(-x)*sum(x**m/math.factorial(m) for m in range(j+1))) for j in range(32))
        cdf_tolerance=.12 if fd else 6*math.sqrt(reference_cdf*(1-reference_cdf)/(n*replicas))
        checks.append(check(name+' CDF de la envolvente en 1',cdf,reference_cdf,cdf_tolerance))
        studies.append({'model':name,'seeds':[2026113040+100*index,2026113040+100*index+replicas-1],
                        'replicas':replicas,'samples':n,'observed_power':float(power),'acf_lag_two':float(lag_two),
                        'envelope_cdf_at_one':float(cdf),'psd_integral':float(spectral_power)})
    phase_noise=apply_phase_noise(source,PhaseNoiseSpec(1.5,2026113400))
    phase_step=np.diff(phase_noise.phase.values.real)
    increments=Signal(phase_step,origin=source.origin+1,metadata={
        'sample_rate_hz':rate,'time_start_s':1/rate,'amplitude_units':'rad'})
    measured=describe_record(increments)
    expected_variance=math.tau*1.5/rate
    checks.append(check('Varianza de incrementos de fase',measured['rms']['value']**2,expected_variance,
                        6*expected_variance*math.sqrt(2/len(phase_step))))
    phase_id=project.add(phase_noise.phase,operation='Ruido de fase',parents=(parent,))
    increments_id=project.add(increments,operation='Incremento de fase',parents=(phase_id,))
    store_statistics(project,measured,[(increments,increments_id,())],'Estadística del incremento')
    artifact=folder/'canales.slproj'
    session.save(artifact,project,session.empty_workspace())
    restored,_=session.load(artifact)
    ctx=ExecutionContext()
    for header in project.headers('signal'):
        key=header['id']
        if content_digest(restored.get(key),ctx.checkpoint)!=content_digest(project.get(key),ctx.checkpoint):
            raise AssertionError('El proyecto modificó un registro de comunicaciones.')
    return {'study':'Realizaciones de canales entre laboratorios','sample_rate_hz':rate,
            'doppler_hz':doppler,'studies':studies,'checks':checks}


DEMONSTRATORS = {'A':distributions,'B':identification,'C':filtering,'D':monte_carlo,'E':channels}


def run(output):
    output.mkdir(parents=True,exist_ok=False)
    receipts={}
    for name, study in DEMONSTRATORS.items():
        folder=output/name
        folder.mkdir(parents=True,exist_ok=True)
        report=study(folder)
        path=folder/'report.json'
        write_json(path,report)
        with path.open('rb') as handle:
            digest=file_digest(handle,'sha256').hexdigest()
        receipts[name]={'passed':True,'sha256':digest,'reference_cases':len(report['checks']),
                        'report':path.relative_to(output).as_posix()}
    return receipts


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    write_json(args.output/'demonstrators.json',run(args.output))
