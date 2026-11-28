"""Independent numerical checks and reproducible RF project fixtures."""

from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

from signallab_pc import session
from signallab_pc.advanced_fourier import chirp_z, zoom_fft
from signallab_pc.analog_design import bessel_prototype, design
from signallab_pc.atomic_file import write_json
from signallab_pc.communications_propagation import FreeSpaceLoss, PropagationSpec
from signallab_pc.model import Signal
from signallab_pc.operations import dft
from signallab_pc.project import Project
from signallab_pc.rf_analysis import cascade, measure
from signallab_pc.rf_application import RFRequest, run_rf, store_rf
from signallab_pc.rf_experiments import matching_sweep
from signallab_pc.rf_line import smith_values, uniform_line
from signallab_pc.rf_link import RFStage, link_budget
from signallab_pc.rf_matching import evaluate_matching, synthesize_matching
from signallab_pc.rf_network import RFNetwork, convert
from signallab_pc.rf_storage import load_network
from signallab_pc.touchstone import read_touchstone
from signallab_pc.window_signals import generate_window
from signallab_pc.window_spectrum import analyze


def _check(label, actual, expected, tolerance):
    actual,expected,tolerance=map(float,(actual,expected,tolerance))
    if not all(map(math.isfinite,(actual,expected,tolerance))) or abs(actual-expected)>tolerance:
        raise AssertionError(f'{label}: {actual:.17g}, referencia {expected:.17g}, tolerancia {tolerance:.3g}.')
    return {'name':label,'actual':actual,'reference':expected,'absolute_tolerance':tolerance}


def _error(label, actual, expected, tolerance):
    return _check(label,np.max(np.abs(np.asarray(actual)-expected)),0,tolerance)


def networks(folder):
    f=np.array([1e6,3e6,5e6])
    impedance=np.array([15+4j,15+10j,15+16j])
    chain=np.broadcast_to(np.eye(2,dtype=complex),(3,2,2)).copy()
    chain[:,0,1]=impedance
    source=RFNetwork(f,chain,representation='ABCD',reference_ohm=[50,75],name='R y L serie')
    through=RFNetwork(f,np.broadcast_to([[0,1],[1,0]],(3,2,2)),reference_ohm=75)
    stage=cascade(source,through)
    denominator=125+impedance
    expected=2*np.sqrt(50*75)/denominator
    result=measure(stage)
    return [
        _error('Transmisión por divisor de tensión y ondas de potencia',stage.values[:,1,0],expected,6e-16),
        _error('Reflexión desde la impedancia vista por el puerto',stage.values[:,0,0],(75+impedance-50)/denominator,1e-15),
        _error('Pérdida de inserción',result.insertion_loss_db[:,1,0],-20*np.log10(abs(expected)),4e-14),
        _error('Reconstrucción de impedancia serie',convert(stage,'ABCD').values[:,0,1],impedance,1e-13),
        _check('Reciprocidad',int(result.reciprocal.all()),1,0),
        _check('Pasividad',int(result.passive.all()),1,0),
    ]


def matching(folder):
    center=1e9
    grid=np.array([.8,1,1.2])*center
    model=uniform_line(grid,0,50,load_ohm=100)
    normalized,_=smith_values(model.input_reference_reflection)
    design,=synthesize_matching('quarter_wave',center,50,100)
    answer=evaluate_matching(design,grid)
    z0=np.sqrt(5000)
    tangent=np.tan((np.pi/2)*grid/center)
    zin=z0*(100+1j*z0*tangent)/(z0+1j*100*tangent)
    return [
        _error('Reflexión de carga de 100 Ω',model.input_reference_reflection,1/3,5e-16),
        _error('Carta de Smith en carga resistiva',normalized,2,2e-15),
        _error('Adaptador de cuarto de onda en banda',answer.input_impedance_ohm,zin,3e-13),
        _check('Potencia entregada en frecuencia de diseño',answer.delivered_power_fraction[1],1,2e-15),
    ]


def filters(folder):
    from scipy.signal import impulse, step
    result=bessel_prototype(2,4,normalization='delay')
    transfer=result['systems'][0]
    w=np.geomspace(.1,20,50)
    s=1j*w/4
    direct=3/(s*s+3*s+3)
    phase=-np.arctan2((s*s+3*s+3).imag,(s*s+3*s+3).real)
    gain=abs(direct)
    delay=np.real((2*s+3)/(s*s+3*s+3))/4
    t=np.linspace(0,2,101)
    _,h=impulse((transfer.b.real,transfer.a.real),T=t)
    _,y=step((transfer.b.real,transfer.a.real),T=t)
    wd=2*np.sqrt(3)
    expected_h=(48/wd)*np.exp(-6*t)*np.sin(wd*t)
    expected_y=1-np.exp(-6*t)*(np.cos(wd*t)+(6/wd)*np.sin(wd*t))
    other=design([1],[10],.3,.2,'compare_rf')['systems']
    return [
        _error('Módulo del polinomio de Bessel',np.abs(transfer.response(w)),gain,1e-14),
        _error('Fase del prototipo',np.angle(transfer.response(w)),phase,1e-14),
        _error('Retardo por derivada del argumento',transfer.group_delay(w),delay,1e-14),
        _error('Impulso del sistema de segundo orden',h,expected_h,1e-13),
        _error('Escalón del sistema de segundo orden',y,expected_y,1e-13),
        _check('Familias disponibles en la comparación',len(other),5,0),
    ]


def link(folder):
    rf=link_budget(20,PropagationSpec(FreeSpaceLoss(100,2e9)),1e6,
                   tx_antenna_dbi=6,rx_antenna_dbi=8,
                   transmit_stages=[RFStage.passive('cable TX',2)],
                   receive_stages=[RFStage.passive('cable RX',1),RFStage('LNA',18,3)],
                   required_snr_db=10)
    path=20*math.log10(4*math.pi*100*2e9/299792458)
    rx_noise=-173.975187194228+60+1+3
    return [
        _check('EIRP de balance manual',rf.eirp_dbm,24,1e-13),
        _check('Potencia de espacio libre',rf.received_at_antenna_dbm,32-path,1e-12),
        _check('Friis de atenuador físico y LNA',rf.noise.input_noise_dbm,rx_noise,1e-11),
        _check('Sensibilidad y margen',rf.margin_db,32-path-rx_noise-10,1e-11),
    ]


def spectra(folder):
    index=np.arange(-25,103)
    source=Signal(1.75*np.exp(1j*(.49*index-.21)),-25,metadata={'sample_rate_hz':1000})
    zoom=zoom_fft(source,.45,.55,101,window='flattop',complex_tone_peaks=1)
    # Flat Top's exact sample at the tone gives the calibration; the local
    # maximum can lie away from the true tone, owing to the nearly flat lobe.
    coeffs=(.21557895,-.41663158,.277263158,-.083578947,.006947368)
    phase=2*np.pi*np.arange(index.size)/(index.size-1)
    weights=sum(coefficient*np.cos(k*phase) for k,coefficient in enumerate(coeffs))
    expected=np.exp(-1j*np.outer(zoom.spectrum.axis,index)) @ (weights*source.values)
    czt=chirp_z(source,128)
    direct=np.exp(-2j*np.pi*np.outer(np.arange(128)/128,index)) @ source.values
    fft=dft(source)
    from signallab_pc.fourier_phase import dft_origin_phase
    shifted=fft.values*dft_origin_phase(np.arange(128),128,int(index[0]))
    peaks=zoom_fft(source,.45,.55,103,window='hann',complex_tone_peaks=1).peaks
    halfbin=analyze(generate_window('boxcar',128))['metrics']['scalloping_db']
    return [
        _error('Zoom FFT con Flat Top frente a suma directa',zoom.spectrum.values,expected,3e-12),
        _error('Chirp-Z sobre unidad frente a suma directa',czt.samples.values,direct,3e-11),
        _error('DFT con origen trasladado frente a suma directa',shifted,direct,3e-11),
        _check('Frecuencia con Hann, tono fuera de bin',peaks[0].refined_frequency,.49,5e-11),
        _check('Amplitud coherente con Hann',peaks[0].amplitude,1.75,5e-11),
        _check('Fase del tono referida a n',peaks[0].phase_rad,-.21,5e-10),
        _check('Pérdida a medio bin rectangular',halfbin,-20*np.log10(1/(128*np.sin(np.pi/256))),1e-12),
    ]


def interchange(folder):
    touchstone=folder/'asymmetry.s2p'
    touchstone.write_text('# MHz S RI R 50\n100 0 0 .8 -.1 .02 0 0 0\n'
                          '200 .2 0 .6 -.1 .01 0 0 0\n',encoding='ascii')
    source=read_touchstone(touchstone)
    req=RFRequest('analyze')
    measured=run_rf(req,(source,))
    project=Project()
    receipt=store_rf(project,measured)
    saved=folder/'experiment.slproj'
    session.save(saved,project,session.empty_workspace())
    reopened,_=session.load(saved)
    restored=load_network(reopened,receipt['product_id'])
    original=sha256(touchstone.read_bytes()).hexdigest()
    design,=synthesize_matching('quarter_wave',100e6,50,100)
    sweep=matching_sweep(design,'resistance_ohm',[80,100,120],restored.frequencies_hz)
    return [
        _error('Orden S21 no recíproco al importar',restored.values[:,1,0],[.8-.1j,.6-.1j],0),
        _check('Huella de entrada retenida',int(restored.metadata['source_sha256']==original),1,0),
        _check('Solicitud y medición guardadas',int(reopened.get(receipt['result_id'])==measured.document()),1,0),
        _error('Barrido de impedancia a cuarto de onda',sweep.reflection[:,0],(100-sweep.values)/(100+sweep.values),9e-16),
        _error('Barrido de impedancia a media onda',sweep.reflection[:,1],(sweep.values-50)/(sweep.values+50),9e-16),
    ]


_STUDIES = {'A':networks,'B':matching,'C':filters,'D':link,'E':spectra,'F':interchange}


def run(root):
    results={}
    for label,case in _STUDIES.items():
        folder=root/label
        folder.mkdir(parents=True,exist_ok=True)
        checks=case(folder)
        report=folder/'report.json'
        write_json(report,{'schema':1,'demonstrator':label,'checks':checks})
        results[label]={'passed':True,'reference_cases':len(checks),'report':report.relative_to(root).as_posix(),
                        'sha256':sha256(report.read_bytes()).hexdigest()}
    return results


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    print(json.dumps(run(parser.parse_args().output),indent=2))
