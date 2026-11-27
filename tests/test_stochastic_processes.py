"""Oracles for conditional laws, covariances and independent path substreams."""

import json
import math
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.execution import ExecutionContext, ResourceLimitError
from signallab_pc.jobs import OperationCancelled
from signallab_pc.project import Project
from signallab_pc.stochastic_processes import Process, generate_process, process_moments, process_transition, store_processes


class ProcessOracles(unittest.TestCase):
    def test_integrated_processes_observe_the_initial_condition_and_correct_time_units(self):
        walk = Process('random_walk', {'initial': 4, 'drift': -2, 'std': 0})
        path = generate_process(walk, 5, 11, origin=-10, rate=20)[0]
        np.testing.assert_array_equal(path.axis, [-10, -9, -8, -7, -6])
        np.testing.assert_array_equal(path.values, [4, 2, 0, -2, -4])
        self.assertEqual(path.metadata['time_start_s'], 0)
        self.assertEqual(process_transition(walk, 3, rate=20)['location_increment']['value'], -6)
        wiener = Process('wiener', {'initial': 1, 'drift': -.5, 'std': 2})
        report = process_moments(wiener, 8, 4, rate=4)
        self.assertEqual(report['offsets'], [8,4])
        self.assertEqual([row['value'] for row in report['means']], [0., .5])
        np.testing.assert_allclose([row['value'] for row in report['variances']], [8,4], rtol=2e-12)
        self.assertEqual(report['covariance']['value'], 4)
        self.assertFalse(report['stationary_initialization'])
        poisson = Process('poisson_process', {'initial': 3, 'event_rate': 4})
        report = process_moments(poisson, 4, 8, rate=4)
        self.assertEqual([row['value'] for row in report['means']], [7,11])
        self.assertEqual(report['covariance']['value'], 4)
        self.assertEqual(process_transition(poisson, 1, rate=4)['event_mean']['value'], 1)
        record = generate_process(poisson, 100, 31, rate=4)[0]
        self.assertEqual(record.values[0], 3)
        self.assertTrue(np.all(np.diff(record.values.real) >= 0))
        self.assertTrue(np.all(record.values.real == np.floor(record.values.real)))

    def test_ou_conditional_law_and_stationary_covariance(self):
        parameters = {'initial': 0, 'mean': 2, 'reversion': .5, 'std': 1}
        model = Process('ornstein_uhlenbeck', parameters)
        transition = process_transition(model, 4, rate=4)
        self.assertAlmostEqual(transition['state_coefficient'], math.exp(-.5), delta=2e-12)
        self.assertAlmostEqual(transition['location_increment']['value'], 2*(1-math.exp(-.5)), delta=2e-12)
        self.assertAlmostEqual(transition['conditional_std']['value']**2, 1-math.exp(-1), delta=2e-12)
        self.assertEqual(process_transition(model, 0, rate=4)['conditional_std']['value'], 0.)
        stats = process_moments(model, 4, 8, rate=4)
        self.assertFalse(stats['stationary_initialization'])
        self.assertAlmostEqual(stats['covariance']['value'], (1-math.exp(-1))*math.exp(-.5), delta=2e-12)
        equilibrium = Process('ornstein_uhlenbeck', {**parameters, 'initial': None})
        stats = process_moments(equilibrium, 4, 8, rate=4)
        self.assertTrue(stats['stationary_initialization'])
        self.assertAlmostEqual(stats['covariance']['value'], math.exp(-.5), delta=2e-12)
        deterministic = Process('ornstein_uhlenbeck', {**parameters, 'std': 0})
        path = generate_process(deterministic, 9000, 9, rate=4)[0]
        moments = process_moments(deterministic, 1, 8193, rate=4)
        self.assertEqual(path.values[0], 0)
        for offset, row in zip(moments['offsets'], moments['means'], strict=True):
            self.assertAlmostEqual(path.values[offset].real, row['value'], delta=2e-12)
        fine_clock = process_transition(model, 1, rate=1e18)
        self.assertAlmostEqual(fine_clock['conditional_std']['value'], 1e-9, delta=2e-21)
        slow = Process('ornstein_uhlenbeck', {'initial':0, 'mean':1e300, 'reversion':1e-16, 'std':0})
        outcome = generate_process(slow, 3, 11, rate=1e6)[0].values.real
        np.testing.assert_allclose(outcome, [0,1e278,2e278], rtol=2e-12)
        self.assertEqual(generate_process(equilibrium, 1, 23, rate=4)[0].values.size, 1)

    def test_finite_chains_and_telegraph_keep_transition_direction(self):
        model = Process('markov', {'initial': 0, 'transition': [[.75, .25], [.5, .5]]})
        report = process_transition(model, 2, rate=100)
        self.assertEqual(report['transition'], [[.6875, .3125], [.625, .375]])
        np.testing.assert_allclose(report['stationary_distribution'], [2/3,1/3], rtol=2e-12)
        stats = process_moments(model, 1, 2)
        np.testing.assert_allclose([x['value'] for x in stats['means']], [.25,.3125], atol=2e-12)
        self.assertAlmostEqual(stats['covariance']['value'], .25*.5 - .25*.3125, delta=2e-12)
        absorbing = Process('markov', {'initial': [0,1], 'transition': [[1,0],[0,1]]})
        self.assertIsNone(process_transition(absorbing, 100)['stationary_distribution'])
        np.testing.assert_array_equal(generate_process(absorbing, 10, 19)[0].values, np.ones(10))
        cycling = Process('markov', {'initial': 1, 'transition': [[0,1],[1,0]]})
        np.testing.assert_array_equal(generate_process(cycling, 5, 3)[0].values, [1,0,1,0,1])
        self.assertEqual(process_transition(cycling, (1 << 61)+1)['transition'], [[0,1],[1,0]])
        periodic = Process('markov', {'initial': 'stationary', 'transition': [[0,1],[1,0]]})
        np.testing.assert_allclose(process_transition(periodic, 1)['initial_distribution'], [.5,.5], rtol=2e-12)
        params = {'initial': 0, 'low': -2, 'high': 1, 'rate_up': 1, 'rate_down': 2}
        telegraph = Process('telegraph', params)
        loss = 1-math.exp(-3)
        law = process_transition(telegraph, 4, rate=4)
        np.testing.assert_allclose(law['transition'], [[1-loss/3,loss/3],[2*loss/3,1-2*loss/3]], rtol=2e-12)
        stationary = Process('telegraph', {**params, 'initial': None})
        result = process_moments(stationary, 4, 8, rate=4)
        self.assertTrue(result['stationary_initialization'])
        self.assertAlmostEqual(result['means'][0]['value'], -1, delta=2e-12)
        self.assertAlmostEqual(result['covariance']['value'], 2*math.exp(-3), delta=2e-12)
        json.dumps(result, allow_nan=False)

    def test_reproducibility_cancellation_and_invalid_models(self):
        model = Process('wiener', {'initial': 0, 'std': 1, 'drift': 0})
        paths = generate_process(model, 64, 119, replicas=2, origin=8, rate=20)
        one = generate_process(model, 64, 119, origin=8, rate=20)[0]
        np.testing.assert_array_equal(paths[0].values, one.values)
        self.assertFalse(np.array_equal(paths[0].values, paths[1].values))
        self.assertEqual(paths[1].metadata['substream'], [1])
        self.assertEqual(paths[1].metadata['sample_rate_hz'], 20)
        with self.assertRaises(ResourceLimitError):
            generate_process(model, 64, 119, rate=20, execution=ExecutionContext(max_work_bytes=1))
        event=Event()
        event.set()
        context=ExecutionContext(cancel=event)
        for method, args in [(generate_process,(model,64,119)),(process_transition,(model,2)),(process_moments,(model,1,2))]:
            with self.assertRaises(OperationCancelled):
                method(*args, rate=4, execution=context)
        for family, options in [
            ('missing', {}), ('random_walk', {}), ('wiener', {'initial': 0, 'std': -1, 'drift': 0}),
            ('markov', {'initial': 0, 'transition': [[0,1]]}),
            ('markov', {'initial': 0, 'transition': [[0,1],[1]]}),
            ('markov', {'initial': [1], 'transition': [[1,0],[0,1]]}),
            ('markov', {'initial': 'stationary', 'transition': [[1,0],[0,1]]}),
            ('telegraph', {'initial': None, 'low':0,'high':0,'rate_up':1,'rate_down':1}),
            ('telegraph', {'initial': None, 'low':0,'high':1,'rate_up':0,'rate_down':0}),
        ]:
            with self.subTest(family=family, options=options), self.assertRaises(ValueError):
                Process(family, options)
        with self.assertRaises(ValueError):
            process_transition(model, 1)
        with self.assertRaises(ValueError):
            generate_process(model, 3, 1, rate=1, origin=(1 << 63)-1)
        poisson = Process('poisson_process', {'initial': (1 << 53)-1,'event_rate':100})
        with self.assertRaises(FloatingPointError):
            generate_process(poisson, 3, 121, rate=1)

    def test_invalid_or_edited_batches_leave_no_model_or_paths_in_the_project(self):
        process = Process('random_walk', {'initial': 0, 'std': 1, 'drift': 0})
        first, second = generate_process(process, 8, 991, replicas=2)
        project = Project()
        with self.assertRaises(ValueError):
            store_processes(project, process.document(), ())
        with self.assertRaises(ValueError):
            store_processes(project, process.document(), [first, second.copy_with()])
        second.values[1] = 9
        with self.assertRaises(ValueError):
            store_processes(project, process.document(), [first, second])
        self.assertEqual(project.headers(), [])

    def test_seeded_ensemble_matches_independent_moments(self):
        seed, replicas = 2026112903, 2048

        def ensemble(family, parameters):
            model = Process(family, parameters)
            paths = generate_process(model, 9, seed, replicas=replicas, rate=4)
            return np.stack([row.values.real for row in paths])

        for family, parameters, means, variances, covariance in [
            ('wiener', {'initial':1,'drift':-.5,'std':2}, [.5,0], [4,8], 4),
            ('ornstein_uhlenbeck', {'initial':0,'mean':2,'reversion':.5,'std':1},
             [2*(1-math.exp(-.5)),2*(1-math.exp(-1))], [1-math.exp(-1),1-math.exp(-2)],
             (1-math.exp(-1))*math.exp(-.5)),
        ]:
            data = ensemble(family,parameters)[:,[4,8]]
            np.testing.assert_array_less(abs(data.mean(axis=0)-means), 6*np.sqrt(np.asarray(variances)/replicas))
            partial = (data[:,0]-means[0])*(data[:,1]-means[1])
            self.assertAlmostEqual(partial.mean(), covariance, delta=6*math.sqrt((math.prod(variances)+covariance**2)/replicas))
        p = ensemble('poisson_process', {'initial':2,'event_rate':4})
        first, second = p[:,4]-2, p[:,8]-p[:,4]
        self.assertAlmostEqual(p[:,8].mean(), 10, delta=6*math.sqrt(8/replicas))
        self.assertAlmostEqual(np.mean((first-4)*(second-4)), 0, delta=24/math.sqrt(replicas))
        for family, parameters, probability in [
            ('telegraph', {'initial':0,'low':0,'high':1,'rate_up':1,'rate_down':2}, (1-math.exp(-6))/3),
            ('markov', {'initial':0,'transition':[[.75,.25],[.5,.5]]}, (1-.25**8)/3),
        ]:
            count = np.count_nonzero(ensemble(family,parameters)[:,8])
            self.assertAlmostEqual(count, replicas*probability, delta=6*math.sqrt(replicas*probability*(1-probability))+1)

    def test_headless_round_trip_preserves_model_path_and_clock(self):
        parameters = {'initial': 0, 'event_rate': 2}
        model = Process('poisson_process', parameters)
        command = ('import sys; sys.modules["PySide6"]=None; '
                   'from signallab_pc.__main__ import main; raise SystemExit(main(sys.argv[1:]))')

        def invoke(verb, args, code=0):
            result = subprocess.run([sys.executable,'-B','-X','utf8','-c',command,'stochastic',verb,
                                     '--family',model.family,'--parameters',json.dumps(parameters),'--rate','8',*args],
                                    text=True, encoding='utf-8', capture_output=True, timeout=20)
            self.assertEqual(result.returncode, code, result.stderr)
            return json.loads(result.stdout) if code == 0 else result.stderr

        report = invoke('inspect', ['--first','2','--second','4'])
        self.assertEqual(report['moments'], process_moments(model,2,4,rate=8))
        self.assertEqual(report['transition'], process_transition(model,2,rate=8))
        with TemporaryDirectory() as root:
            file = Path(root)/'paths.slproj'
            args = ['--count','64','--seed','115','--replicas','2','--origin','-5','--output',str(file)]
            receipt = invoke('generate', args)
            project, _ = session.load(file)
            self.assertEqual(project.get(receipt['model_id']), model.document())
            for stored, expected in zip(receipt['result_ids'], generate_process(model,64,115,replicas=2,origin=-5,rate=8), strict=True):
                record = project.get(stored)
                self.assertEqual(record.origin, -5)
                self.assertEqual(record.metadata, expected.metadata)
                np.testing.assert_array_equal(record.values, expected.values)
            saved = file.read_bytes()
            self.assertIn('presupuesto', invoke('generate', [*args,'--max-work-bytes','1'], 1))
            self.assertEqual(file.read_bytes(), saved)
