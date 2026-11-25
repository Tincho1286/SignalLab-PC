"""Reproduce the Engineering Core examples in Python or from a notebook."""

from argparse import ArgumentParser
from pathlib import Path
from threading import Event
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from signallab_pc import session
from signallab_pc.dft_application import DFTRequest, calculate_dft
from signallab_pc.dsp_application import (
    FIRDesignRequest, FIRRequest, IDFTRequest, PSDRequest, ResampleRequest,
    apply_fir, calculate_idft, design_fir, estimate_psd, resample,
)
from signallab_pc.dsp_pipeline import DSPPipelineRequest, estimate_pipeline_memory, run_pipeline, store_pipeline
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.scientific_storage import load_binary_signal, save_binary_signal
from signallab_pc.storage import save_json


def demo(directory):
    path=Path(directory)
    path.mkdir(parents=True,exist_ok=True)
    time=np.arange(128)/600
    x=Signal(np.cos(2*np.pi*30*time),-4,metadata={'sample_rate_hz':600,
                                                  'time_start_s':-.25,'amplitude_units':'V'})
    inverse=calculate_idft(IDFTRequest(calculate_dft(DFTRequest(x)).spectrum))
    np.testing.assert_allclose(inverse.values,x.values,atol=1e-13)
    design=design_fir(FIRDesignRequest('lowpass',9,.18))
    output=apply_fir(FIRRequest(x,design.transfer,'full'))
    converted=resample(ResampleRequest(x,2,3))
    power=estimate_psd(PSDRequest(output,method='periodogram',window='boxcar',sidedness='one-sided'))

    request=DSPPipelineRequest(ResampleRequest(x,2,3,return_filter=True),design.transfer,
                               psd_method='periodogram',psd_window='boxcar')
    memory=estimate_pipeline_memory(request).total_bytes
    context=ExecutionContext(max_work_bytes=memory,pool=ResourcePool(memory))
    result=run_pipeline(request,context)
    project=Project()
    ids=store_pipeline(project,request,result,execution=context)
    session.save(path/'resultados.json',project,session.empty_workspace(),before_commit=context.checkpoint)
    project,_=session.load(path/'resultados.json')
    np.testing.assert_array_equal(project.get(ids.filtered).values,result.filtered.values)
    save_json(x,path/'entrada.json')
    save_binary_signal(x,path/'entrada.slbin')
    np.testing.assert_array_equal(load_binary_signal(path/'entrada.slbin').values,x.values)

    cancelled=Event()
    cancelled.set()
    try:
        run_pipeline(request,ExecutionContext(cancel=cancelled))
    except OperationCancelled:
        pass
    else:
        raise AssertionError('La ejecución debía cancelar.')
    return {'inverse':inverse,'fir':output,'resampled':converted.signal,'psd':power,'records':ids}


if __name__=='__main__':
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    print(demo(args.directory)['records'])
