"""Independent correlation, covariance and alignment oracles."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.execution import ExecutionContext, ResourceLimitError
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.scientific_storage import save_binary_signal
from signallab_pc.statistics_results import store_statistics
from signallab_pc.stochastic_cli import main
from signallab_pc.stochastic_covariance import covariance_matrix, ensemble_moments, estimate_correlation
from signallab_pc.stochastic_processes import Process, generate_process, process_moments


def correlation_oracle(first, second, lag, divisor, normalized):
    values = []
    count = len(first)
    factor = (sum(abs(x)**2 for x in first)*sum(abs(y)**2 for y in second))**.5/count
    for k in range(-lag,lag+1):
        products = [first[i+k]*second[i].conjugate() for i in range(count) if 0 <= i+k < count]
        scale = count if divisor == 'N' else len(products)
        values.append(sum(products) / (scale * (factor if normalized else 1)))
    return values


def complex_array(data):
    return np.asarray(data['real']) + 1j*np.asarray(data['imag'])


class CovarianceOracles(unittest.TestCase):
    def test_alignment_sign_and_conjugation_for_close_and_broad_lags(self):
        x = [10,1+2j,2-1j,-1j,4,6j]
        y = [-1j,3,2+2j,-1,5]
        meta = {'sample_rate_hz': 4, 'time_start_s': 0.}
        first = Signal(x, origin=-1, metadata=meta)
        second = Signal(y, origin=0, metadata={**meta, 'time_start_s': .25})
        x, y = x[1:], y[:]
        for method in ('direct','fft','auto'):
            for divisor, normalize in [('N',False),('overlap',True)]:
                result = estimate_correlation(first,second,max_lag=4,method=method,denominator=divisor,normalize=normalize)
                expected = correlation_oracle(x,y,4,divisor,normalize)
                np.testing.assert_allclose(result.values, expected, atol=2e-12)
                self.assertEqual(result.metadata['common_origin'], 0)
                self.assertEqual(result.metadata['common_last_index'], 4)
                self.assertEqual(result.metadata['time_start_s'], -1)
                self.assertEqual(result.metadata['pair_count_rule'], 'N−|k|')
        broad = estimate_correlation(Signal(np.r_[np.ones(20),0]), max_lag=12)
        self.assertTrue(broad.metadata['method'].startswith('FFT'))

    def test_centering_and_hermitian_autocovariance(self):
        samples = [4-2j, -1+1j, 2j, -3-1j]
        signal = Signal(samples)
        centered = [value-sum(samples)/len(samples) for value in samples]
        for method in ('direct','fft'):
            result = estimate_correlation(signal,max_lag=3,remove_mean=True,normalize=True,method=method)
            np.testing.assert_array_equal(result.values, np.conj(result.values[::-1]))
            np.testing.assert_allclose(result.values, correlation_oracle(centered,centered,3,'N',True), atol=2e-12)
            self.assertEqual(result.values[3], 1)
        pair = estimate_correlation(signal,signal,max_lag=3,remove_mean=True)
        np.testing.assert_allclose(pair.values, correlation_oracle(centered,centered,3,'N',False), atol=2e-12)
        very_small = Signal([1e-200,-1e-200])
        self.assertEqual(estimate_correlation(very_small,max_lag=0).metadata['underflowed_samples'], 1)

    def test_complex_matrices_against_outer_products(self):
        samples = np.array([[1,1j,2],[2j,0,2],[3,1+3j,2],[0,2,2]],complex)
        channels = [Signal(samples[:,i],name=f'Canal {i}',metadata={'amplitude_units':'V'}) for i in range(3)]
        centered = samples - samples.mean(axis=0)
        expected = sum(np.outer(row,row.conj()) for row in centered)/(len(samples)-1)
        expected_pseudo = sum(np.outer(row,row) for row in centered)/(len(samples)-1)
        result = covariance_matrix(channels)
        covariance = complex_array(result['covariance'])
        np.testing.assert_allclose(covariance, expected, atol=2e-12)
        np.testing.assert_allclose(complex_array(result['pseudocovariance']), expected_pseudo, atol=2e-12)
        np.testing.assert_array_equal(covariance,covariance.conj().T)
        self.assertGreaterEqual(np.min(np.linalg.eigvalsh(covariance)), -1e-12)
        self.assertEqual(result['correlation']['real'][2], [None,None,None])
        self.assertEqual(result['correlation']['real'][0][0], 1.)
        self.assertEqual(result['amplitude_units'], ['V']*3)
        large = covariance_matrix((Signal([1e200,-1e200]),))
        self.assertEqual(large['covariance']['real'], [[None]])
        self.assertEqual(large['correlation']['real'], [[1.]])
        json.dumps(large,allow_nan=False)

    def test_ensemble_describes_samples_across_traces_not_time_averages(self):
        traces = [Signal([base,base+delta],origin=11,name=f'Réplica {base}') for base,delta in [(1,1),(3,3),(5,5)]]
        result = ensemble_moments(traces,0,1)
        self.assertEqual(result['means'], [[3.,0.],[6.,0.]])
        self.assertEqual(result['divisor'], 2)
        np.testing.assert_array_equal(complex_array(result['covariance']), [[4,8],[8,16]])
        self.assertEqual(result['increment_mean'][0]['value'], 3.)
        self.assertEqual(result['increment_variance']['value'], 4.)
        reversed_time = ensemble_moments(traces,1,0,sample=False)
        self.assertEqual(reversed_time['increment_mean'][0]['value'],-3.)
        self.assertAlmostEqual(reversed_time['increment_variance']['value'],8/3)
        paths = [Signal([3,4], metadata={'sample_rate_hz':2,'time_start_s':2}) for _ in range(2)]
        self.assertEqual(ensemble_moments(paths,0,1)['replicas'],2)

    def test_invalid_geometry_and_budget_reject_observable_changes(self):
        source = Signal([1,1],origin=0)
        with self.assertRaises(ValueError):
            estimate_correlation(source, normalize=True, remove_mean=True)
        with self.assertRaises(ValueError):
            estimate_correlation(Signal([1e200,-1e200]), max_lag=0)
        for other in (Signal([2,3],origin=7), Signal([1,2],domain='continuous'), 'sin(n)'):
            with self.subTest(other=other), self.assertRaises(ValueError):
                estimate_correlation(source,other)
        known = Signal([1,2],metadata={'sample_rate_hz':8,'time_start_s':0})
        incompatible = Signal([1,2],metadata={'sample_rate_hz':8,'time_start_s':1})
        with self.assertRaises(ValueError):
            covariance_matrix([source,known,incompatible])
        with self.assertRaises(ValueError):
            covariance_matrix([])
        with self.assertRaises(ValueError):
            covariance_matrix([Signal([1])])
        for paths in ([], [source], [source,source], [source,known],
                      [source,Signal([1,2,3])], [source,Signal([1,2],metadata={'amplitude_units':'m'})]):
            with self.assertRaises(ValueError):
                ensemble_moments(paths,0,1)
        self.assertEqual(covariance_matrix([Signal([1])],sample=False)['covariance']['real'],[[0.]])
        self.assertNotIn('sample_rate_hz', estimate_correlation(source,known).metadata)
        event = Event()
        event.set()
        for operation, args in [(estimate_correlation, (source,)),
                               (covariance_matrix,([source],)),
                               (ensemble_moments,([source,source.copy_with()],0,1))]:
            with self.assertRaises(OperationCancelled):
                operation(*args, execution=ExecutionContext(cancel=event))
            with self.assertRaises(ResourceLimitError):
                operation(*args, execution=ExecutionContext(max_work_bytes=1))

    def test_shared_model_compares_theory_and_reused_substreams_are_rejected(self):
        model = Process('wiener', {'initial':2., 'std':.3, 'drift':.1})
        first, second = generate_process(model,5,11,replicas=2,rate=4)
        result = ensemble_moments((first,second),1,3)
        self.assertEqual(result['recorded_model_reference'],process_moments(model,1,3,rate=4))
        with self.assertRaisesRegex(ValueError, 'subflujo'):
            ensemble_moments((first,first.copy_with()),1,3)
        invalid_model = {'schema':1,'process':'incompatible','parameters':{}}
        historical = [record.copy_with(metadata={**record.metadata, 'model':invalid_model}) for record in (first,second)]
        result = ensemble_moments(historical,1,3)
        self.assertIn('reference_notice',result)
        self.assertEqual(result['replicas'], 2)

    def test_two_uses_of_the_same_parent_remain_one_verified_project_reference(self):
        project = Project()
        source, other = Signal([1,2]), Signal([3,2])
        parent = project.add(source)
        result = estimate_correlation(source,source)
        keys, stored = store_statistics(project, result, [(source,parent,()),(source,parent,())], result.name)
        self.assertEqual(keys,[parent,parent])
        self.assertEqual(project.headers()[-1]['parents'], [parent])
        np.testing.assert_array_equal(project.get(stored).values,result.values)
        before = project.headers()
        conflicting = estimate_correlation(source,other)
        with self.assertRaises(ValueError):
            store_statistics(project, conflicting, [(source,parent,()),(other,parent,())], conflicting.name)
        self.assertEqual(project.headers(),before)

    def test_cli_methods_persist_completed_reports_and_reject_bad_references(self):
        project = Project()
        data = (Signal([1,2]),Signal([3,6]))
        ids = [project.add(signal) for signal in data]
        def invoke(command, code=0):
            stdout, stderr = StringIO(),StringIO()
            with redirect_stdout(stdout),redirect_stderr(stderr):
                self.assertEqual(main(command),code,stderr.getvalue())
            return json.loads(stdout.getvalue()) if code == 0 else stderr.getvalue()
        with TemporaryDirectory() as directory:
            base, output, first_file, second_file = (Path(directory)/name for name in ['base.slproj','out.slproj','first.slbin','second.slbin'])
            session.save(base,project,session.empty_workspace())
            save_binary_signal(data[0],first_file)
            save_binary_signal(data[1],second_file)
            options = ['--session',str(base),'--output',str(output)]
            result = invoke(['correlate', *options, '--record',ids[0],'--second-record',ids[1],'--method','fft'])
            loaded,_ = session.load(output)
            np.testing.assert_array_equal(loaded.get(result['result_id']).values,estimate_correlation(*data,method='fft').values)
            for method, extra, expected in [('matrix',[],covariance_matrix(data)),
                                            ('ensemble',['--independent'],ensemble_moments(data,0,1))]:
                result = invoke([method,*options,'--records',*ids,*extra])
                loaded,_ = session.load(output)
                self.assertEqual(loaded.get(result['result_id']), expected)
            self.assertIn('independencia', invoke(['ensemble',*options,'--records',*ids],1))
            self.assertIn('distintos',invoke(['matrix',*options,'--records',ids[0],ids[0]],1))
            options = ['correlate','--signal',str(first_file),'--output',str(output)]
            self.assertIn('sesión',invoke([*options,'--second-record',ids[1]],1))
            self.assertIn('salida', invoke([*options,'--second-signal',str(output)],1))
            result = invoke([*options,'--second-signal',str(second_file)])
            self.assertEqual(len(result['source_ids']),2)
