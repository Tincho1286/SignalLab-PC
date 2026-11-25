from dataclasses import replace
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest

from numpy.testing import assert_allclose

from signallab_pc import session
from signallab_pc.dsp_application import ResampleRequest
from signallab_pc.dsp_pipeline import DSPPipelineRequest, PipelineStageError, run_pipeline, store_pipeline
from signallab_pc.execution import ExecutionContext
from signallab_pc.filters import Transfer
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.storage import save_json
from test_math_dft_pilot import cli, direct_sum


def case(up=1, down=1):
    source = Signal([1,2,-1,0,3,1], -2,
                    metadata={'sample_rate_hz':12, 'time_start_s':-.25, 'amplitude_units':'V'})
    return DSPPipelineRequest(ResampleRequest(source,up,down,half_width=3,return_filter=True),
                              Transfer([.5,.5],[1]), psd_method='periodogram',
                              psd_window='boxcar', amplitude_units='V')


class DSPPipelineTests(unittest.TestCase):
    def test_exact_filter_spectrum_psd_and_lineage(self):
        request=case()
        result=run_pipeline(request)
        expected=[.5,1.5,.5,-.5,1.5,2]
        assert_allclose(result.filtered.values,expected)
        assert_allclose(result.dft.spectrum.values,direct_sum(result.filtered,6,True,'sample_indices'))
        assert_allclose(result.psd.values.real,abs(result.dft.spectrum.values)**2/72)
        self.assertEqual(result.psd.metadata['density_units'],'V²/Hz')
        project=Project()
        records=store_pipeline(project,request,result)
        parents={record['id']:record['parents'] for record in project.headers()}
        self.assertEqual(parents[records.filtered],[records.resampled,records.filter])
        self.assertEqual(parents[records.psd],parents[records.dft])
        self.assertEqual(parents[records.psd],[records.filtered])

    def test_clock_units_errors_and_cancelling_at_each_handoff(self):
        request=case(2,3)
        for percentage in (25,50,75):
            with self.subTest(percentage=percentage):
                event=Event()
                progress=[]
                def notify(value):
                    progress.append(value)
                    if value >= percentage:event.set()
                with self.assertRaises(OperationCancelled):
                    run_pipeline(request,ExecutionContext(cancel=event,progress=notify))
                self.assertEqual(progress,sorted(progress))
                self.assertEqual(progress[-1],percentage)
        with self.assertRaisesRegex(PipelineStageError,'Entrada'):
            run_pipeline(replace(request,amplitude_units='A'))
        with self.assertRaisesRegex(PipelineStageError,'FIR'):
            run_pipeline(replace(request,fir=Transfer([1],[1],sample_period_s=1/12)))

    def test_headless_cli_matches_pipeline_and_preserves_destination_on_error(self):
        request=case(2,3)
        with TemporaryDirectory() as directory:
            source, target=(Path(directory)/name for name in ('input.json','session.json'))
            save_json(request.conversion.signal,source)
            args=('dsp-pipeline','--signal',source,'--output',target,'--up',2,'--down',3,
                  '--fir',.5,.5,'--psd-method','periodogram','--window','boxcar')
            # The CLI defaults to the existing converter's half-width of 10.
            default=replace(request,conversion=replace(request.conversion,half_width=10))
            result=run_pipeline(default)
            command=cli(*args)
            self.assertEqual(command.returncode,0,command.stderr)
            ids=json.loads(command.stdout)
            project,_=session.load(target)
            assert_allclose(project.get(ids['dft']).values,result.dft.spectrum.values)
            self.assertEqual(project.get(ids['filtered']).metadata['sample_rate_hz'],8)
            previous=target.read_bytes()
            failed=cli(*args,'--length',0)
            self.assertEqual(failed.returncode,1)
            self.assertIn('DFT',failed.stderr)
            self.assertEqual(target.read_bytes(),previous)
