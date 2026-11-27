import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event

import numpy as np

from signallab_pc import session
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.kalman_filter import kalman_filter, store_kalman
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError
from signallab_pc.state_space import StateModel
from signallab_pc.stochastic_cli import main


class KalmanFilterTests(unittest.TestCase):
    def test_scalar_filter_equals_batch_conditioning_with_known_controls(self):
        a, b, c, d, q, r, p0 = .8, .25, 2., .5, .2, .7, 1.25
        u = np.asarray([[0],[2],[-1],[.5],[0]])
        observed = np.asarray([True,False,True,False,True])
        measurements = np.asarray([3, -99, 5, -99, 4.])
        model = StateModel([[a]], [[b]], [[c]], [[d]], .125)
        result = kalman_filter(model, measurements[:,None], [[q]], [[r]], [2], [[p0]],
                               controls=u, mask=observed[:,None])
        count = len(u)
        # Direct joint covariance of all the states as functions of independent increments.
        phis = np.asarray([[a**(i-k) if k<=i else 0. for k in range(count)] for i in range(count)])
        state_cov = (phis*np.array([p0,*([q]*(count-1))])) @ phis.T
        state_mean = phis @ np.r_[2., b*u[:-1,0]]
        residual_observation = measurements - (c*state_mean + d*u[:,0])
        for current in range(count):
            for before, estimated, covariance in ((True,result.predicted,result.prior_covariance),
                                                    (False,result.corrected,result.posterior_covariance)):
                indices = np.flatnonzero(observed[:current + int(not before)])
                covariance_y = c*c*state_cov[np.ix_(indices,indices)] + r*np.eye(len(indices))
                cross_covariance = c*state_cov[current,indices]
                weights = np.linalg.solve(covariance_y, cross_covariance)
                self.assertAlmostEqual(estimated[current,0].real, state_mean[current]+weights @ residual_observation[indices])
                self.assertAlmostEqual(covariance[current,0,0].real, state_cov[current,current]-weights @ cross_covariance)
        self.assertEqual(result.report['prediction_only_steps'], 2)
        np.testing.assert_array_equal(result.measurements[~observed], 0)
        np.testing.assert_array_equal(result.gains[~observed], 0)

    def test_complex_partial_observations_preserve_cross_covariances_and_conjugation(self):
        p = np.asarray([[3,.25j],[-.25j,2]])
        sensors = np.asarray([[1,1j],[2,-1j],[0,1]])
        model = StateModel(np.eye(2), np.zeros((2,1)), sensors, np.zeros((3,1)), 1.)
        noise = np.array([[1,0,.2j],[0,2,0],[-.2j,0,3]])
        measurement = np.asarray([2+1j, 14-20j, 1])
        mask = np.array([[True,False,True]])
        result = kalman_filter(model, [measurement], np.zeros((2,2)), noise, [0,0], p, mask=mask)
        sensor, covariance = sensors[mask[0]], noise[np.ix_(mask[0],mask[0])]
        gain = np.linalg.solve(sensor @ p @ sensor.conj().T + covariance, sensor @ p).conj().T
        np.testing.assert_allclose(result.gains[0][:,mask[0]], gain, atol=1e-14)
        np.testing.assert_allclose(result.corrected[0], gain @ measurement[mask[0]], atol=1e-14)
        residual = np.eye(2)-gain @ sensor
        joseph = residual @ p @ residual.conj().T + gain @ covariance @ gain.conj().T
        np.testing.assert_allclose(result.posterior_covariance[0], joseph, atol=1e-14)
        self.assertGreaterEqual(np.linalg.eigvalsh(result.posterior_covariance[0]).min(), 0)
        self.assertEqual(result.report['missing_components'],1)

    def test_exact_and_very_precise_observations_keep_positive_covariance(self):
        model = StateModel([[1]], [[0]], [[1]], [[0]], 1.)
        result = kalman_filter(model, [[2],[2]], [[0]], [[0]], [0], [[1]])
        np.testing.assert_array_equal(result.corrected[:,0], [2,2])
        np.testing.assert_array_equal(result.posterior_covariance, 0)
        with self.assertRaisesRegex(ValueError, 'restricción determinista'):
            kalman_filter(model, [[2],[3]], [[0]], [[0]], [0], [[1]])
        result = kalman_filter(model, [[2]], [[0]], [[1e-30]], [0], [[1]])
        self.assertAlmostEqual(result.posterior_covariance[0,0,0].real/1e-30,1)

    def test_input_shapes_indefiniteness_resources_and_mid_iteration_cancellation(self):
        model = StateModel([[1]], [[0]], [[1]], [[0]], 1.)
        for data,q,r,initial,prior,options in (
            ([[1,2]],[[0]],[[1]],[0],[[1]],{}),
            ([[1]],[[0]],[[1]],[0,1],[[1]],{}),
            ([[1]],[[0]],[[1]],[0],[[1]],{'controls':[[0],[1]]}),
            ([[1]],[[0]],[[1]],[0],[[1]],{'mask':[[0]]}),
            ([[1]],[[0]],[[1]],[0],[[1,0],[0,1]],{}),
            ([[1]],[[-1]],[[1]],[0],[[1]],{}),
        ):
            with self.subTest(data=data, options=options), self.assertRaises(ValueError):
                kalman_filter(model,data,q,r,initial,prior,**options)
        with self.assertRaises(ValueError):
            kalman_filter(StateModel([[1]],[[0]],[[1]],[[0]]),[[1]],[[0]],[[1]],[0],[[1]])
        with self.assertRaises(ResourceLimitError):
            kalman_filter(model,[[1]],[[0]],[[1]],[0],[[1]],execution=ExecutionContext(max_work_bytes=1))
        event = Event()
        context = ExecutionContext(cancel=event, progress=lambda value: event.set() if value>=50 else None)
        with self.assertRaises(OperationCancelled):
            kalman_filter(model,[[1],[2],[3],[4]],[[0]],[[1]],[0],[[1]],execution=context)

    def test_verified_receipt_rejects_changed_model_and_can_reopen_all_records(self):
        model = StateModel([[1]], [[0]], [[1]], [[0]], .25)
        project = Project()
        other = project.add(StateModel([[2]], [[0]], [[1]], [[0]], .25))
        result = kalman_filter(model, [[2],[4]], [[0]], [[1]], [0], [[1]])
        with self.assertRaisesRegex(ValueError, 'origen registrado'):
            store_kalman(project, model, result, model_id=other, origin=-7)
        self.assertEqual(len(project.headers()),1)
        saved = store_kalman(project, model, result, origin=-7)
        with TemporaryDirectory() as folder:
            path = Path(folder)/'states.slproj'
            session.save(path,project,session.empty_workspace())
            project,_ = session.load(path)
        trace = project.get(saved['outputs'][1][0])
        self.assertEqual(trace.origin,-7)
        self.assertAlmostEqual(trace.metadata['time_start_s'],-1.75)
        np.testing.assert_allclose(trace.values,[1,2])
        self.assertEqual(project.get(saved['report'])['mask'],[[True],[True]])
        model.C[0,0]=.5
        with self.assertRaisesRegex(ValueError,'modelo cambió'):
            store_kalman(project, model, result, origin=-7)

    def test_cli_persists_partially_observed_data_and_outputs(self):
        spec = {'state_model': {'A':[[1]],'B':[[0]],'C':[[1]],'D':[[0]],'dt':.5},
                'observations': [[2],[13],[10]],'process_covariance':[[0]],'measurement_covariance':[[1]],
                'initial_mean':[0],'initial_covariance':[[1]],'mask':[[True],[False],[True]]}
        with TemporaryDirectory() as folder:
            model, workspace = (Path(folder)/name for name in ('state.json','result.slproj'))
            model.write_text(json.dumps(spec), encoding='utf-8')
            stdout, stderr = StringIO(), StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = main(['kalman','--model',str(model),'--output',str(workspace)])
            self.assertEqual(code,0,stderr.getvalue())
            saved = json.loads(stdout.getvalue())
            result,_ = session.load(workspace)
            np.testing.assert_allclose(result.get(saved['outputs'][1]).values,[1,1,4])
            self.assertEqual(result.get(saved['report'])['observations_per_sample'],1)
            self.assertEqual(result.headers('calculation')[0]['parents'],[saved['model']])
