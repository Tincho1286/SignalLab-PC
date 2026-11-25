import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from numpy.testing import assert_allclose

from signallab_pc import session
from signallab_pc.model import Signal
from signallab_pc.scientific_storage import save_binary_signal
from signallab_pc.storage import save_json
from test_math_dft_pilot import cli


class CoreCLITests(unittest.TestCase):
    def execute(self, output, *args):
        result=cli(*args,'--output',output)
        self.assertEqual(result.returncode,0,result.stderr)
        project,_=session.load(output)
        receipt=json.loads(result.stdout)
        return project,receipt

    def test_individual_commands_share_session_and_binary_input(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/'source.slbin'
            save_binary_signal(Signal([1,2,-3,4],-2,metadata={'sample_rate_hz':8}),source)
            _, D=self.execute(root/'dft.json','dft','--signal',source)
            inverse,I=self.execute(root/'idft.json','dsp','idft','--session',root/'dft.json','--record',D['result_id'])
            assert_allclose(inverse.get(I['result_id']).values,[1,2,-3,4],atol=1e-13)
            self.assertEqual(inverse.get(I['result_id']).origin,-2)
            converted,C=self.execute(root/'resample.json','dsp','resample','--signal',source,'--up',1,'--down',2)
            self.assertEqual(converted.get(C['result_id']).metadata['sample_rate_hz'],4.)
            power,P=self.execute(root/'psd.json','dsp','psd','--signal',source,'--method','periodogram',
                                 '--window','boxcar','--sidedness','one-sided')
            measured=power.get(P['result_id'])
            self.assertAlmostEqual(float(measured.values.real.sum()*measured.step),7.5)

    def test_fir_design_and_application_commands(self):
        with TemporaryDirectory() as directory:
            root=Path(directory)
            source=root/'source.slbin'
            save_binary_signal(Signal([1,0,0]),source)
            model,key=self.execute(root/'design.json','dsp','fir-design','--kind','lowpass',
                                   '--taps',3,'--f1',.25,'--window','boxcar')
            self.assertEqual(model.get(key['specification_id'])['taps'],3)
            applied,A=self.execute(root/'applied.json','dsp','fir','--signal',source,
                                   '--coefficients',.25,.5,.25,'--mode','full')
            assert_allclose(applied.get(A['result_id']).values,[.25,.5,.25,0,0])

    def test_cli_rejects_unsafe_destination_and_respects_expired_deadline(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'input.json', root / 'result.json'
            save_json(Signal([1, 2, 3]), source)
            original = source.read_bytes()
            output.write_bytes(b'previous session')
            for target, options, fragment in (
                    (source, (), 'distinto'),
                    (output, ('--timeout', '1e-12'), 'plazo'),
                    (output, ('--max-work-bytes', '1'), 'presupuesto')):
                result = cli('dft', '--signal', source, '--output', target, *options)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(fragment, result.stderr)
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(output.read_bytes(), b'previous session')
