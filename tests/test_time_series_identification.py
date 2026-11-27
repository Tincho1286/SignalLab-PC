"""Independent residual and forecast oracles for conditional time-series fits."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest

import numpy as np

from signallab_pc import session
from signallab_pc.ar_estimation import fit
from signallab_pc.execution import ExecutionContext, ResourceLimitError
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.random_models import analyze, fit_ar, realization, summary
from signallab_pc.stochastic_cli import main
from signallab_pc.time_series_identification import arma_diagnostics, arma_forecast, arma_system, compare_arma, fit_arma, store_arma_result


class TimeSeriesIdentification(unittest.TestCase):
    def test_stationary_ma_covariance_spectrum_and_realization_are_consistent(self):
        theta, mean, sigma = .4, 2., 3.
        model = analyze([1,theta],[1],mean,sigma,max_lag=4,points=9)
        self.assertAlmostEqual(model.mean,mean*(1+theta))
        self.assertAlmostEqual(model.variance,sigma**2*(1+theta**2))
        expected = [0,0,0,sigma**2*theta,model.variance,sigma**2*theta,0,0,0]
        np.testing.assert_allclose(model.signals[0].values,expected,atol=2e-12)
        np.testing.assert_allclose(model.signals[1].values,np.asarray(expected)+model.mean**2,atol=2e-12)
        omega=model.signals[2].axis
        np.testing.assert_allclose(model.signals[2].values,sigma**2*(1+theta**2+2*theta*np.cos(omega)),atol=2e-12)
        sample=realization(model,32,14,origin=7)
        self.assertEqual(sample.origin,7)
        np.testing.assert_array_equal(sample.values,realization(model,32,14,origin=7).values)
        self.assertEqual(sample.metadata['theoretical_variance'],model.variance)
        self.assertIn('Varianza', summary(model).plain_text())
        unit=analyze([2],[1],noise_mean=1,noise_std=1,points=5)
        np.testing.assert_array_equal(realization(unit,5,12).values,2+2*np.random.Generator(np.random.PCG64(12)).standard_normal(5))

    def test_legacy_yule_walker_matches_shared_convention(self):
        x=[2,3,5,7,9,-2,4,-1,2,1,5,-2,3,4]
        source=Signal(x,origin=-4,metadata={'sample_rate_hz':20.,'time_start_s':3.})
        model=fit_ar(source,2,max_lag=6,points=9)
        expected=fit(source,2,method='yw')
        np.testing.assert_allclose(model.system.a,expected['a'],atol=2e-12)
        self.assertAlmostEqual(model.fit['innovation_variance'],expected['innovation_variance']['value'])
        self.assertEqual(model.signals[-1].origin,-2)
        self.assertEqual(model.signals[-1].metadata['time_start_s'],3.1)
        self.assertIn('Yule',summary(model).plain_text())
        for values,order in [([0,0,0],1),([1,1,1],1),([1,2],2),([0,1,2j],1)]:
            with self.assertRaises(ValueError):
                fit_ar(Signal(values),order)

    def test_theoretical_analysis_rejects_invalid_processes_instead_of_returning_covariance(self):
        for b,a,std,points in [([1],[1,-1.0],1.,5),([1j],[1],1.,5),([1],[1],-1.,5),([1],[1],1.,2),
                               ([1],[1],1e200,5)]:
            with self.subTest(a=a,b=b,std=std),self.assertRaises(ValueError):
                analyze(b,a,noise_std=std,points=points)

    def test_conditional_ar_matches_regression_on_same_sample(self):
        values = [-1,2,1,2,1,-1,4,3,-2,1,3,3,1,0,2]
        source = Signal(values)
        ar = fit(source,1,method='ols',hold_back=2)
        model = fit_arma(source,1,0,hold_back=2)
        self.assertEqual(model['fitted_samples'], ar['nfit'])
        np.testing.assert_allclose(model['a'], ar['a'],atol=2e-7)
        self.assertAlmostEqual(model['innovation_variance']['value'],ar['innovation_variance']['value'],delta=2e-12)
        for key in ('aic','aicc','bic'):
            self.assertAlmostEqual(model[key],ar[key],delta=2e-11)
        self.assertTrue(model['stationary_levels'])

    def test_ma_forecast_uses_the_last_innovation_and_analytic_variance(self):
        source = Signal([4,4.5,2,4,2,5,6,3,8,9,7,8,7,4],origin=-4)
        fit = fit_arma(source,0,1)
        self.assertTrue(fit['identifiable'])
        theta = fit['b'][1]
        mean = fit['mean_differenced']
        residual = 0
        for observation in source.values.real:
            residual = observation-mean-theta*residual
        result = arma_forecast(source,fit,3)
        central = [mean+theta*residual,mean,mean]
        expected_width = 1.959963984540054*np.sqrt(fit['innovation_variance']['value']*np.array([1,1+theta**2,1+theta**2]))
        self.assertEqual(result['signals'][0].origin,10)
        np.testing.assert_allclose(result['signals'][0].values,central,atol=2e-12)
        np.testing.assert_allclose(result['signals'][1].values,central-expected_width,atol=2e-12)
        np.testing.assert_allclose(result['signals'][2].values,central+expected_width,atol=2e-12)

    def test_arma_seeded_recovery_and_reserved_data(self):
        innovations = np.random.Generator(np.random.PCG64(2026112906)).standard_normal(4096+512)
        values = np.zeros(len(innovations))
        for i in range(1,len(values)):
            values[i] = .65*values[i-1]+innovations[i]+.4*innovations[i-1]
        train = values[512:]
        a = fit_arma(Signal(np.r_[train,1,2,4]),1,1,validation=3)
        b = fit_arma(Signal(np.r_[train,10,30,40]),1,1,validation=3)
        self.assertAlmostEqual(-a['a'][1], .65,delta=.08)
        self.assertAlmostEqual(a['b'][1], .4,delta=.08)
        self.assertEqual(a['a'],b['a'])
        self.assertEqual(a['b'],b['b'])
        self.assertNotEqual(a['validation_mse'],b['validation_mse'])
        self.assertTrue(a['invertible'] and a['identifiable'])

    def test_integrated_forecast_and_uncertainty_in_the_original_levels(self):
        values = [0,3,4,7,11,12,14,25]
        source = Signal(values,origin=10,metadata={'sample_rate_hz':4,'time_start_s':2,'amplitude_units':'V'})
        result = fit_arma(source,0,0,differences=1,validation=1)
        increments = [b-a for a,b in zip(values[:6],values[1:7])]
        drift = sum(increments)/len(increments)
        variance = sum((v-drift)**2 for v in increments)/len(increments)
        self.assertAlmostEqual(result['mean_differenced'],drift)
        self.assertAlmostEqual(result['innovation_variance']['value'],variance)
        self.assertTrue(result['stationary_core'])
        self.assertFalse(result['stationary_levels'])
        forecast = arma_forecast(source,result,4)['signals']
        steps = np.arange(1,5)
        expected = values[-1] + steps*drift
        width = 1.959963984540054*np.sqrt(steps*variance)
        np.testing.assert_allclose(forecast[0].values,expected,atol=2e-12)
        np.testing.assert_allclose(forecast[1].values,expected-width,atol=2e-12)
        np.testing.assert_allclose(forecast[2].values,expected+width,atol=2e-12)
        self.assertEqual(forecast[0].metadata['time_start_s'],4.)
        self.assertEqual(forecast[0].metadata['amplitude_units'],'V')
        self.assertEqual(forecast[0].origin,18)

    def test_degenerate_fit_resource_limits_and_residual_scope(self):
        with self.assertRaises(ValueError):
            fit_arma(Signal([1,2,3]),1,1)
        with self.assertRaises(ValueError):
            fit_arma(Signal([1,2,3,4,5,6]),0,1,differences=1)
        with self.assertRaises(ValueError):
            fit_arma(Signal([1,2j,3]),0,0)
        source = Signal([2,4,6,8,10])
        result = fit_arma(source,0,0,differences=1)
        self.assertTrue(result['near_exact'])
        self.assertIsNone(result['aic'])
        predicted = arma_forecast(source,result,3)
        self.assertEqual(len(predicted['signals']),1)
        np.testing.assert_array_equal(predicted['signals'][0].values,[12,14,16])
        with self.assertRaises(ValueError):
            arma_forecast(Signal([2,4,6,8,12]),result,3)
        with self.assertRaises(ValueError):
            arma_forecast(source,result,3,coverage=1)
        event = Event()
        event.set()
        for operation,args in [(fit_arma,(source,0,0)),(arma_forecast,(source,result,3))]:
            with self.assertRaises(ResourceLimitError):
                operation(*args,execution=ExecutionContext(max_work_bytes=1))
            with self.assertRaises(OperationCancelled):
                operation(*args,execution=ExecutionContext(cancel=event))

    def test_second_difference_forecast_accumulates_error_twice(self):
        source=Signal([0,1,3,7,11,12,15,16])
        fit = fit_arma(source,0,0,differences=2)
        result = arma_forecast(source,fit,3)['signals']
        drift = fit['mean_differenced']
        step = np.arange(1,4)
        expected = 16+step+drift*step*(step+1)/2
        variance = fit['innovation_variance']['value']
        np.testing.assert_allclose(result[0].values,expected,atol=2e-12)
        np.testing.assert_allclose(result[2].values-expected,1.959963984540054*np.sqrt(variance*np.cumsum(step**2)),atol=2e-12)

    def test_diagnostics_and_selection_use_the_same_support(self):
        x = [4,4.5,2,4,2,5,6,3,8,9,7,8,7,4,7,6,8,6,9,7]
        source = Signal(x,origin=-8,metadata={'sample_rate_hz':16,'time_start_s':1})
        fits = compare_arma(source,[(0,0),(1,0),(0,1),(30,30)],validation=0)
        self.assertIsNone(fits['selected'])
        self.assertTrue(all('error' in row for row in fits['rows']))
        fits = compare_arma(source,[(0,0),(1,0),(0,1),(1,1)],differences=1,validation=3)
        self.assertEqual({row['fitted_samples'] for row in fits['rows']},{15})
        self.assertEqual({row['hold_back'] for row in fits['rows']},{1})
        selectable = [i for i,row in enumerate(fits['rows']) if row['bic'] is not None]
        self.assertEqual(fits['selected'],min(selectable,key=lambda i:fits['rows'][i]['bic']))
        row = fits['rows'][2]
        diag = arma_diagnostics(source,row,4)
        model = arma_system(source,row,levels=True)
        np.testing.assert_array_equal(model.a,[1,-1])
        self.assertEqual(model.sample_period_s,1/16)
        expected = []
        last = 0.
        for delta in np.diff(x):
            last = delta - row['mean_differenced'] - row['b'][1]*last
            expected.append(last)
        np.testing.assert_allclose(diag['signals'][1].values,expected[1:],atol=2e-12)
        np.testing.assert_allclose(diag['signals'][0].values+diag['signals'][1].values, x[2:],atol=2e-12)
        self.assertEqual(diag['signals'][0].origin,-6)
        self.assertEqual(diag['signals'][0].metadata['time_start_s'],1.125)
        self.assertIsNone(diag['rows'][0]['p_value'])
        self.assertTrue(0 <= diag['rows'][-1]['p_value'] <= 1)
        with self.assertRaises(ValueError):
            compare_arma(source,[(0,0)],criterion='validation')
        self.assertIsNotNone(compare_arma(source,[(0,0),(0,1)],validation=4,criterion='validation')['selected'])

    def test_console_reopens_fit_and_predictions_as_one_verified_study(self):
        source = Signal([1,3,5,6,9,10,9,14,15,14,17,18],origin=-4)
        project = Project()
        parent = project.add(source)
        with TemporaryDirectory() as folder:
            base, out = Path(folder)/'base.slproj',Path(folder)/'fit.slproj'
            session.save(base,project,session.empty_workspace())
            args = ['identify','--session',str(base),'--record',parent,'--output',str(out),
                    '--d','1','--reserve','2','--horizon','3','--lags','4']
            stdout,stderr=StringIO(),StringIO()
            with redirect_stdout(stdout),redirect_stderr(stderr):
                self.assertEqual(main(args),0,stderr.getvalue())
            ids = json.loads(stdout.getvalue())
            reopened,_ = session.load(out)
            fitted = reopened.get(ids['result_id'])
            expected = fit_arma(source,0,0,differences=1,validation=2)
            self.assertEqual({key:fitted[key] for key in expected},expected)
            next_step = reopened.get(ids['signal_ids'][-3])
            np.testing.assert_array_equal(next_step.values,arma_forecast(source,expected,3)['signals'][0].values)
            self.assertEqual(reopened.headers()[-1]['parents'],[ids['result_id']])
            self.assertEqual(ids['source_id'],parent)
            before=out.read_bytes()
            with redirect_stderr(stderr):
                self.assertEqual(main([*args,'--max-work-bytes','1']),1)
            self.assertEqual(out.read_bytes(),before)
        with self.assertRaises(ValueError):
            store_arma_result(project,source.copy_with(values=np.arange(12)),parent,expected,arma_system(source,expected),())
        self.assertEqual(len(project.headers()),1)
