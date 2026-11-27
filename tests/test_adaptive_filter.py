import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event

import numpy as np

from signallab_pc import session
from signallab_pc.adaptive_filter import adaptive_fir, compare_adaptive, store_adaptive_comparison
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError
from signallab_pc.stochastic_cli import main


class AdaptiveFilterTests(unittest.TestCase):
    def test_lms_traces_a_priori_prediction_and_holds_final_coefficients_fixed(self):
        result = adaptive_fir(Signal([1,2,3,4]), Signal([2,4,6,8]), length=1, method='lms', step=.1, reserve=2)
        np.testing.assert_allclose(result.estimate.values, [0,.4,2.76,3.68], atol=2e-15)
        self.assertAlmostEqual(result.system.b[0].real,.92)
        self.assertAlmostEqual(result.report['validation_mse']['value'], (3.24**2+4.32**2)/2)

    def test_nlms_uses_complex_gradient_and_handles_zero_input(self):
        x = np.asarray([0,2j,1,2+1j])
        d = np.asarray([4,.5+1j,3+.25j,1])
        expected = []
        h = 0j
        for component, target in zip(x,d):
            estimated = component*h
            expected.append(estimated)
            h += .8*(target-estimated)*component.conjugate()/(abs(component)**2+.25)
        result = adaptive_fir(Signal(x),Signal(d),length=1,method='nlms',step=.8,floor=.25)
        np.testing.assert_allclose(result.estimate.values, expected, atol=2e-15)
        self.assertAlmostEqual(result.system.b[0],h)

    def test_complex_rls_matches_independent_weighted_ridge_at_each_time(self):
        x = np.asarray([3+1j,-2j,4,1-3j,-1+4j,-2,4+2j,-1])
        d = np.asarray([2,1-2j,4,5,2j,-1+2j,1-3j,2])
        length, forget, ridge, reserve = 2, .8, .125, 2
        rows = np.array([[x[i],x[i-1]] for i in range(1,len(x))])
        target = d[1:]
        end = len(rows)-reserve
        prediction = []
        for index,row in enumerate(rows):
            count = min(index,end)
            weight = forget**np.arange(count-1,-1,-1)
            design = np.r_[np.sqrt(weight)[:,None]*rows[:count], np.sqrt(ridge*forget**count)*np.eye(length)]
            rhs = np.r_[np.sqrt(weight)*target[:count],np.zeros(length)]
            h = np.linalg.lstsq(design,rhs,rcond=None)[0]
            prediction.append(row@h)
        result = adaptive_fir(Signal(x),Signal(d),length=length,method='rls',forgetting=forget,ridge=ridge,reserve=reserve)
        np.testing.assert_allclose(result.estimate.values,prediction,atol=2e-14)
        np.testing.assert_allclose(result.system.b,h,atol=2e-14)

    def test_prediction_uses_past_only_and_stores_delay_in_the_fir(self):
        record = Signal([2,3,5,1,4,-1,2], -5, metadata={'sample_rate_hz':8,'time_start_s':4})
        result = adaptive_fir(record,length=2,purpose='prediction',method='lms',step=.03,delay=2)
        self.assertEqual(result.estimate.origin,-2)
        self.assertEqual(result.estimate.metadata['time_start_s'],4+3/8)
        self.assertEqual(result.estimate.values[0],0)
        np.testing.assert_allclose(result.system.b[:2],0)
        self.assertEqual(result.system.sample_period_s,.125)
        self.assertEqual(len(result.report['input_hashes']),1)

    def test_rls_noise_cancellation_recovers_clean_reference_on_holdout(self):
        drive = np.tile([1.,-1,1,-1],50)
        clean = np.tile([1.,1,-1,-1],50)
        observed = clean+3*drive
        result = adaptive_fir(Signal(drive),Signal(observed),length=1,method='rls',
                              purpose='cancellation',forgetting=1.,ridge=.01,reserve=32)
        clean_estimate = result.error.values[-32:]
        np.testing.assert_allclose(clean_estimate,clean[-32:],atol=.0002)
        self.assertEqual(result.error.name,'Estimación limpia')

    def test_invalid_combinations_and_cancelled_comparison_leave_no_results(self):
        x = Signal([1,2,3,4,0,-1])
        cases = (
            ({'method':'unknown'},x), ({'purpose':'prediction','delay':0},None),
            ({'purpose':'prediction'},x), ({'method':'rls','step':.1},x),
            ({'method':'rls','forgetting':2},x), ({'method':'lms','floor':.1},x),
            ({'method':'nlms','step':2},x), ({'reserve':99},x), ({},None),
        )
        for params,desired in cases:
            with self.subTest(params=params), self.assertRaises(ValueError):
                adaptive_fir(x,desired,length=1,**params)
        configs = [{'method':'lms','step':.1},{'method':'rls'}]
        with self.assertRaises(ResourceLimitError):
            compare_adaptive(x,x,configs,length=1,execution=ExecutionContext(max_work_bytes=2880))
        with self.assertRaises(ValueError):
            compare_adaptive(x,x,[{'method':'rls','delay':2}],length=1)
        result = compare_adaptive(x,x,configs,length=1)
        event = Event()
        checks = []

        class CancelBeforePublishProject(Project):
            def stage_records(self, *, before_commit):
                def guard():
                    checks.append(1)
                    event.set()
                    before_commit()
                return super().stage_records(before_commit=guard)

        project = CancelBeforePublishProject()
        with self.assertRaises(OperationCancelled):
            store_adaptive_comparison(project,result,[(x,None,()),(x,None,())],execution=ExecutionContext(cancel=event))
        self.assertTrue(checks)
        self.assertEqual(project.headers(), [])

    def test_cli_comparison_reopens_common_input_lineage_and_distinct_outputs(self):
        project = Project()
        x = Signal([1,2,3,-4,5,1,0,3])
        y = Signal(x.values*2)
        incoming, desired = project.add(x), project.add(y)
        with TemporaryDirectory() as folder:
            source,configuration,destination = (Path(folder)/name for name in ('signal.slproj','methods.json','out.slproj'))
            session.save(source,project,session.empty_workspace())
            configuration.write_text('[{"method":"lms","step":0.03},{"method":"rls","forgetting":1}]',encoding='utf-8')
            stdout,stderr = StringIO(),StringIO()
            with redirect_stdout(stdout),redirect_stderr(stderr):
                code = main(['adaptive','--session',str(source),'--record',incoming,'--second-record',desired,
                             '--length','1','--reserve','3','--configurations',str(configuration),'--output',str(destination)])
            self.assertEqual(code,0,stderr.getvalue())
            receipt = json.loads(stdout.getvalue())
            saved,_ = session.load(destination)
        comparison = saved.get(receipt['comparison'])
        self.assertEqual([row['method'] for row in comparison['rows']],['lms','rls'])
        self.assertEqual([run['sources'] for run in receipt['runs']],[[incoming,desired]]*2)
        self.assertLess(comparison['rows'][1]['validation_mse']['value'],comparison['rows'][0]['validation_mse']['value'])
