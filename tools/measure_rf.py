"""Native Phase 06 throughput, memory, cancellation, and Workbench timing."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import platform
from statistics import median
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
from time import perf_counter

from check_engineering_baseline import clean_revision
from check_resource_limits import peak_rss

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

import numpy as np

from signallab_pc import session
from signallab_pc.advanced_fourier import chirp_z, zoom_fft
from signallab_pc.analog_design import bessel_prototype
from signallab_pc.atomic_file import write_json
from signallab_pc.communications_propagation import PropagationSpec
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.rf_analysis import cascade, measure
from signallab_pc.rf_experiments import LinkUncertainty, link_campaign, matching_sweep
from signallab_pc.rf_line import uniform_line
from signallab_pc.rf_link import link_budget
from signallab_pc.rf_matching import synthesize_matching
from signallab_pc.rf_network import RFNetwork, convert
from signallab_pc.rf_storage import load_network, store_network
from signallab_pc.touchstone import read_touchstone, write_touchstone


class RecordingPool(ResourcePool):
    def __init__(self):
        super().__init__(256*1024**2)
        self.maximum=0

    def reserve(self,amount):
        self.maximum=max(self.maximum,amount)
        return super().reserve(amount)


def multiport(scale,ctx,folder):
    f=np.linspace(1e6,1e8,scale*2048)
    diagonal=np.arange(4)*.05+.15
    net=RFNetwork(f,np.broadcast_to(np.diag(diagonal),(len(f),4,4)),context=ctx)
    z=convert(net,'Z',context=ctx)
    measures=measure(net,context=ctx)
    assert measures.passive.all()
    np.testing.assert_allclose(z.values[0].diagonal(),50*(1+diagonal)/(1-diagonal))
    return {'points':len(f),'ports':4}


def chain(scale,ctx,folder):
    f=np.linspace(1e6,1e8,scale*8192)
    line=uniform_line(f,30,attenuation_db_per_m=.07,context=ctx)
    joined=cascade(line.network,line.network,context=ctx)
    np.testing.assert_allclose(np.abs(joined.values[:,1,0]),10**(-4.2/20),atol=1e-14)
    return {'points':len(f),'stages':2}


def interchange(scale,ctx,folder):
    count=scale*4096
    f=np.linspace(1e6,1e8,count)
    net=uniform_line(f,.65,context=ctx).network
    path=folder/'measured.ts'
    write_touchstone(path,net,context=ctx)
    reopened=read_touchstone(path,context=ctx)
    np.testing.assert_array_equal(net.values,reopened.values)
    return {'points':count,'transfer_bytes':path.stat().st_size}


def filters(scale,ctx,folder):
    count=scale*8192
    grid=np.linspace(0,10,count)
    def evaluate():
        model=bessel_prototype(8,3,normalization='delay')['systems'][0]
        return model.group_delay(grid)
    result=ctx.run(evaluate,work_bytes=160*(count+4099))
    assert np.isfinite(result).all() and abs(result[0]-1/3)<1e-13
    return {'points':count,'order':8}


def spectra(scale,ctx,folder):
    count=scale*8192
    source=Signal(np.ones(count),-32)
    zoom=zoom_fft(source,-.1,.1,scale*2048+1,context=ctx)
    finite=chirp_z(Signal(np.ones(257),-12),scale*1025,radius_ratio=1.000025,
                   initial_angle_rad=-.1,angle_step_rad=.0001,context=ctx)
    np.testing.assert_allclose(zoom.spectrum.values[scale*1024],count,rtol=1e-13)
    np.testing.assert_allclose(finite.samples.values[-1],np.sum(finite.z[-1]**(-np.arange(-12,245))),atol=2e-12)
    return {'samples':count,'zoom_points':scale*2048+1,'contour_points':scale*1025}


def uncertainty(scale,ctx,folder):
    count=scale*16
    f=np.linspace(.75e9,1.25e9,257)
    design,=synthesize_matching('quarter_wave',1e9,50,100)
    sweep=matching_sweep(design,'resistance_ohm',np.linspace(70,130,count),f,context=ctx)
    margin=link_budget(-160,PropagationSpec(),1,context=ctx)
    result=link_campaign([LinkUncertainty('enlace',margin,1)],folder/'campaign',seed=17645,
                         replicas=scale*24,samples=256,context=ctx)
    assert len(result.replicas)==scale*24
    np.testing.assert_allclose(sweep.reflection[:,128],(100-sweep.values)/(100+sweep.values),atol=1e-15)
    return {'sweep_values':count,'frequencies':len(f),'replicas':len(result.replicas)}


def archive(scale,ctx,folder):
    size=scale*16384
    net=uniform_line(np.linspace(1e6,1e7,size),.1,context=ctx).network
    project=Project()
    key=store_network(project,net,context=ctx)
    path=folder/'experiment.slproj'
    session.save(path,project,session.empty_workspace(),checkpoint=ctx.checkpoint)
    reopened,_=session.load(path,checkpoint=ctx.checkpoint)
    np.testing.assert_array_equal(load_network(reopened,key,context=ctx).values,net.values)
    return {'points':size,'file_bytes':path.stat().st_size}


PROFILES={
    'multiport':multiport,'cascade':chain,'touchstone':interchange,'filter':filters,
    'spectral':spectra,'uncertainty':uncertainty,'archive':archive,
}


def _cancellation():
    with TemporaryDirectory(prefix='sl-rf-cancel-') as directory:
        folder=Path(directory)
        count=2048
        network=uniform_line(np.arange(1,count+1)*1e6,.03).network
        path=folder/'sample.ts'
        write_touchstone(path,network)
        checkpoint=Event()
        release=Event()
        canceled=Event()
        spent=[]

        class PausedContext(ExecutionContext):
            def checkpoint(self,percentage=None):
                spent.append(1)
                if len(spent)==64:
                    checkpoint.set()
                    if not release.wait(5):
                        raise TimeoutError('La prueba de cancelación no recibió la señal.')
                return super().checkpoint(percentage)

        with ThreadPoolExecutor(1) as workers:
            future=workers.submit(read_touchstone,path,context=PausedContext(cancel=canceled))
            if not checkpoint.wait(5):
                raise TimeoutError('La importación no alcanzó el punto de control.')
            start=perf_counter()
            canceled.set()
            release.set()
            try:
                future.result(timeout=3)
            except OperationCancelled:
                elapsed=perf_counter()-start
            else:
                raise RuntimeError('La importación cancelada publicó un resultado.')
        np.testing.assert_array_equal(read_touchstone(path).values,network.values)
    return {'discarded':True,'operation':'touchstone_import','seconds_after_request':elapsed,'retry':True}


def _desktop():
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication
    from signallab_pc.workbench import WorkbenchWindow
    from signallab_pc.workspaces import ROUTES
    start=perf_counter()
    app=QApplication([])
    with TemporaryDirectory(prefix='sl-rf-desktop-') as directory:
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(QSettings.Format.IniFormat,QSettings.Scope.UserScope,directory)
        window=WorkbenchWindow(recovery_directory=Path(directory))
        window.show()
        app.processEvents()
        startup=perf_counter()-start
        routes=[ROUTES['rf',task] for task in ('network','line','link','spectral')]
        def open_route(route):
            before=perf_counter()
            window.open_tool(route)
            app.processEvents()
            return perf_counter()-before
        cold=[open_route(route) for route in routes]
        hot=[open_route(route) for _ in range(4) for route in routes]
        pane=window.pages[routes[1]].panel
        pane.calculate()
        deadline=perf_counter()+15
        while window._workers and perf_counter()<deadline:
            app.processEvents()
        if pane.active_result is None:
            raise RuntimeError('El Workbench no mostró la red calculada.')
        before=perf_counter()
        pane.draw()
        pane.canvas.draw()
        render=perf_counter()-before
        window.hide()
        window.deleteLater()
        app.processEvents()
    return {'seconds_startup':startup,'cold_open_seconds':dict(zip(('network','line','link','spectral'),cold,strict=True)),
            'warm_navigation_median_seconds':median(hot),'warm_navigation_max_seconds':max(hot),
            'seconds_render':render,'peak_rss_bytes':peak_rss(),'platform_plugin':app.platformName(),'verified':True}


def _trial(name,scale):
    if name=='desktop':
        return _desktop()
    if name=='cancel':
        return _cancellation()
    pool=RecordingPool()
    ctx=ExecutionContext(pool=pool)
    with TemporaryDirectory(prefix='sl-rf-profile-') as directory:
        start=perf_counter()
        parameters=PROFILES[name](scale,ctx,Path(directory))
        seconds=perf_counter()-start
    return {'verified':True,'scale':scale,'seconds':seconds,'peak_rss_bytes':peak_rss(),
            'max_observed_reservation_bytes':pool.maximum,'parameters':parameters}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--trial',choices=(*PROFILES,'desktop','cancel'))
    parser.add_argument('--scale',type=int,choices=(1,2),default=1)
    args=parser.parse_args()
    if args.trial:
        write_json(args.output,_trial(args.trial,args.scale))
        return
    revision=clean_revision()
    env=os.environ|{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
                    'BLIS_NUM_THREADS':'1','QT_QPA_PLATFORM':'offscreen'}
    with TemporaryDirectory(prefix='sl-rf-evidence-') as directory:
        def trial(name,scale=1):
            target=Path(directory)/f'{name}-{scale}.json'
            subprocess.run([sys.executable,'-B','-X','utf8',__file__,'--output',str(target),'--trial',name,
                            '--scale',str(scale)],env=env,cwd=ROOT,check=True,timeout=110)
            return json.loads(target.read_bytes())
        report={'schema':1,'phase':'06','commit':revision,'clean_checkout':True,'platform':platform.platform(),
                'threads':1,'profiles':{name:[trial(name,1),trial(name,2)] for name in PROFILES},
                'cancellation':trial('cancel'),'desktop':trial('desktop')}
    if clean_revision()!=revision:
        raise RuntimeError('La revisión cambió durante los perfiles RF.')
    write_json(args.output,report)


if __name__=='__main__':
    main()
