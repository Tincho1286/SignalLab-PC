"""Independent finite-sample oracles and headless descriptive analysis."""

from fractions import Fraction
from pathlib import Path
import json
import math
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.descriptive_statistics import describe_record, project_samples
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.probability import Distribution
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError
from signallab_pc.scientific_storage import save_binary_signal


class DescriptiveStatisticsTests(unittest.TestCase):
    def test_moments_empirical_probabilities_and_boxplot(self):
        observations = [1, 1, 2, 3, 100]
        result = describe_record(Signal(observations), diagnostics=True)
        center = Fraction(sum(observations), len(observations))
        variance = sum((x - center)**2 for x in observations) / len(observations)
        self.assertEqual(result['mean']['value'], float(center))
        self.assertEqual(result['median']['value'], 2)
        self.assertAlmostEqual(result['variance_N']['value'], float(variance), delta=1e-11)
        self.assertAlmostEqual(result['variance_N_minus_1']['value'],
                               float(variance * Fraction(5, 4)), delta=1e-11)
        self.assertAlmostEqual(result['central_moments'][3]['value'],
                               float(sum((x-center)**3 for x in observations)/5), delta=1e-9)
        self.assertAlmostEqual(result['raw_moments'][4]['value'], sum(x**4 for x in observations) / 5)
        self.assertEqual(result['mode']['values'], [1])
        self.assertEqual(result['iqr']['value'], 2)
        self.assertEqual(result['mad']['value'], 1)
        self.assertEqual(result['empirical'], {'x': [1, 2, 3, 100], 'cdf': [.4, .6, .8, 1.],
                                               'survival': [.6, .4, .2, 0.]})
        self.assertEqual(result['boxplot']['outliers'], 1)
        self.assertEqual([datum['value'] for datum in result['boxplot']['whiskers']], [1, 3])

    def test_finite_projections_and_principal_phase(self):
        source = Signal([0, np.exp(1j*(math.pi-.01)), np.exp(-1j*(math.pi-.01))])
        angles = describe_record(source, 'phase')
        self.assertEqual(angles['excluded'], 1)
        self.assertEqual(angles['units'], 'rad')
        self.assertEqual(angles['mean']['value'], 0)
        self.assertAlmostEqual(abs(angles['circular']['mean_direction_rad']['value']), math.pi)
        self.assertAlmostEqual(angles['circular']['circular_variance']['value'], 1-math.cos(.01))
        orthogonal = describe_record(Signal([1,-1]), 'phase')
        self.assertEqual(orthogonal['circular']['mean_direction_rad']['status'], 'undefined')
        self.assertAlmostEqual(describe_record(source,'magnitude')['mean']['value'], 2/3)
        self.assertEqual(describe_record(Signal([2+4j,3+8j]), 'imag')['mean']['value'], 6)
        with self.assertRaises(ValueError):
            describe_record(Signal([0]), 'phase')
        with self.assertRaises(ValueError):
            describe_record(Signal([complex(1.7e308,1.7e308)]), 'magnitude')

    def test_quantiles_and_mean_survive_extreme_scales(self):
        result = describe_record(Signal([-1e300, 1e-200, 1e300]), diagnostics=True)
        self.assertEqual(result['median']['value'], 1e-200)
        self.assertEqual(result['mean']['value'], 1e-200 / 3)
        self.assertEqual(result['mad']['value'], 1e300)
        self.assertEqual(result['variance_N']['status'], 'overflow')
        self.assertIsNone(result['variance_N']['value'])
        json.dumps(result, allow_nan=False)
        wide = describe_record(Signal([-1.7e308, 1.7e308]))
        self.assertEqual(wide['iqr']['value'], 1.7e308)
        self.assertEqual(wide['rms']['value'], 1.7e308)
        flat = describe_record(Signal([1.7e308, 1.7e308]))
        self.assertEqual(flat['mean']['value'], 1.7e308)
        self.assertEqual(flat['skewness']['status'], 'undefined')
        distant = describe_record(Signal([1.7e308, 1.7e308, -1.7e308]))
        self.assertEqual(distant['mad']['value'], 0)

    def test_reference_positions_and_one_sample(self):
        normal = Distribution('normal', {'mean': 0, 'std': 1})
        result = describe_record(Signal([1]), diagnostics=True, reference=normal)
        self.assertEqual(result['variance_N_minus_1']['status'], 'undefined')
        self.assertEqual(result['qq']['probabilities'], [.5])
        self.assertEqual(result['qq']['theoretical'][0]['value'], 0)
        self.assertEqual(result['qq']['observed'], [1])
        self.assertAlmostEqual(result['empirical']['reference_cdf'][0]['value'],
                               .5 + .5 * math.erf(1 / math.sqrt(2)))
        nearest = describe_record(Signal([-1, 0, 1, 40]), reference=normal, diagnostics=True, qq_points=2)
        self.assertEqual(nearest['empirical']['reference_axis'], [-1, 40])
        self.assertEqual(nearest['qq']['observed'], [-1, 40])

    def test_invalid_controls_and_execution_limits(self):
        signal = Signal([1, 2])
        for arguments in (
            {'component': 'amplitude'}, {'probabilities': ()}, {'probabilities': (1.1,)},
            {'reference': object()}, {'qq_points': 0},
        ):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                describe_record(signal, **arguments)
        with self.assertRaises(ValueError):
            describe_record(np.asarray([1, 2]))
        with self.assertRaises(ValueError):
            project_samples([1, 2], 'real')
        with self.assertRaises(ResourceLimitError):
            describe_record(signal, diagnostics=True, execution=ExecutionContext(max_work_bytes=1))
        cancel = Event()
        cancel.set()
        with self.assertRaises(OperationCancelled):
            describe_record(signal, execution=ExecutionContext(cancel=cancel))

    def test_console_reopens_descriptive_report_and_parent(self):
        signal = Signal([1,3,1,4], origin=-2, metadata={'sample_rate_hz': 90})
        normal = Distribution('normal', {'mean':0, 'std':1})
        with TemporaryDirectory() as folder:
            base = Path(folder)/'source.slproj'
            out = Path(folder)/'result.slproj'
            project = Project()
            parent = project.add(signal)
            session.save(base, project, session.empty_workspace())
            command = ('import sys; sys.modules["PySide6"]=None; '
                       'from signallab_pc.__main__ import main; raise SystemExit(main(sys.argv[1:]))')
            result = subprocess.run(
                [sys.executable,'-B','-X','utf8','-c',command,'statistics','describe','--session',str(base),
                 '--record',parent,'--output',str(out),'--reference-family','normal','--reference-parameters',
                 '{"mean":0,"std":1}'],
                text=True, encoding='utf-8', capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            ids = json.loads(result.stdout)
            reopened, _ = session.load(out)
            self.assertEqual(ids['source_id'], parent)
            row = next(item for item in reopened.headers() if item['id'] == ids['result_id'])
            self.assertEqual(row['parents'], [parent])
            self.assertEqual(reopened.get(ids['result_id']), describe_record(signal, diagnostics=True, reference=normal))

    def test_console_accepts_a_signal_and_checks_reference_options(self):
        from contextlib import redirect_stderr, redirect_stdout
        from io import StringIO
        from signallab_pc.statistics_cli import main

        with TemporaryDirectory() as folder:
            signal = Signal([-1,2,3], origin=4)
            source = Path(folder)/'registro.slbin'
            output = Path(folder)/'estadistica.slproj'
            save_binary_signal(signal, source)
            arguments = ['describe','--signal',str(source),'--output',str(output),'--quantiles','0','1']
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(main(arguments), 0)
            ids = json.loads(stdout.getvalue())
            project, _ = session.load(output)
            self.assertEqual(project.get(ids['result_id']), describe_record(signal, probabilities=(0,1)))
            previous = output.read_bytes()
            with redirect_stderr(stderr):
                self.assertEqual(main([*arguments, '--reference-family','normal']), 1)
            self.assertIn('--reference-family y --reference-parameters', stderr.getvalue())
            self.assertEqual(output.read_bytes(), previous)
