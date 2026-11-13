"""Independent regression sums, common-sample scores, clock and real panel actions."""
import os,math,tempfile,csv,json,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from scipy import signal,stats
from signallab_pc.model import Signal
from signallab_pc import ar_estimation as ar


class Arithmetic(unittest.TestCase):
    def test_ols_ar1_against_scalar_regression_and_gaussian_scores(self):
        x=np.array([2.,-1,4,1,3,2,6,-2,1,5]);source=Signal(x);row=ar.fit(source,1)
        previous=x[:-1];target=x[1:];phi=float(sum((previous-previous.mean())*(target-target.mean()))/sum((previous-previous.mean())**2));c=float(target.mean()-phi*previous.mean());errors=target-c-phi*previous
        assert_allclose(row['phi'],[phi],atol=1e-14);self.assertAlmostEqual(row['intercept'],c)
        mse=float(np.mean(errors**2));self.assertAlmostEqual(row['residual_mse']['value'],mse)
        deviance=len(errors)*(math.log(math.tau)+1+math.log(mse));self.assertAlmostEqual(row['aic'],deviance+6);self.assertAlmostEqual(row['bic'],deviance+3*math.log(len(errors)));self.assertAlmostEqual(row['aicc'],row['aic']+24/(len(errors)-4))

    def test_reserved_values_do_not_change_coefficients_but_do_change_validation(self):
        x=np.random.default_rng(12).normal(size=80);first=ar.fit(Signal(x),2,validation=12)
        x[-12:]+=100;second=ar.fit(Signal(x),2,validation=12)
        self.assertEqual(first['a'],second['a']);self.assertEqual(first['intercept'],second['intercept']);self.assertGreater(second['validation_mse']['value'],first['validation_mse']['value']*100)

    def test_order_comparison_uses_same_observations_and_keeps_failed_rows(self):
        source=Signal(np.random.default_rng(3).normal(size=120));result=ar.compare(source,5,validation=20)
        self.assertEqual({r['fit_start'] for r in result['rows']},{5});self.assertEqual({r['nfit'] for r in result['rows']},{95});self.assertEqual(result['selected'],min(range(6),key=lambda i:result['rows'][i]['bic']))
        flat=ar.compare(Signal(np.ones(50)),3);self.assertIsNone(flat['selected']);self.assertFalse(flat['rows'][0]['error']);self.assertTrue(all(r['error'] for r in flat['rows'][1:]));self.assertTrue(flat['rows'][0]['near_exact'])

    def test_ar_zero_and_small_sample_criteria_have_explicit_domains(self):
        source=Signal([0,1,-1]);row=ar.fit(source,0);self.assertEqual(row['a'],[1]);self.assertAlmostEqual(row['intercept'],0);self.assertIsNone(row['aicc']);self.assertIsNotNone(row['bic'])
        with self.assertRaises(ValueError):ar.compare(source,1)
        with self.assertRaises(ValueError):ar.compare(Signal(np.arange(30)),2,criterion='validation')
        with self.assertRaises(ValueError):ar.fit(source,1.5)
        with self.assertRaises(ValueError):ar.fit(source,10**1000)
        with self.assertRaises(ValueError):ar.fit(Signal([1,2j,3,4]),0)

    def test_yule_walker_matches_direct_toeplitz_without_holdout_leakage(self):
        from scipy.linalg import toeplitz
        x=signal.lfilter([1],[1,-.6,.2],np.random.default_rng(6).normal(size=100));row=ar.fit(Signal(x),2,method='yw',validation=20)
        centered=x[:80]-np.mean(x[:80]);cov=np.array([np.dot(centered[k:],centered[:80-k])/80 for k in range(3)]);expected=np.linalg.solve(toeplitz(cov[:2]),cov[1:])
        assert_allclose(row['phi'],expected,atol=1e-13);self.assertAlmostEqual(row['innovation_variance']['value'],cov[0]-expected@cov[1:]);self.assertIsNone(row['aic'])

    def test_residual_diagnostic_matches_direct_lag_sums_and_q(self):
        source=Signal(np.random.default_rng(11).normal(size=130),-7,metadata={'sample_rate_hz':20.,'time_start_s':3.});row=ar.fit(source,2,validation=20);data=ar.diagnostics(source,row,6)
        residual=data['signals'][1].values.real[:row['nfit']].copy();residual-=residual.mean();n=len(residual);rho=np.array([np.dot(residual[k:],residual[:n-k])/np.dot(residual,residual) for k in range(7)])
        q=n*(n+2)*sum(rho[1:]**2/(n-np.arange(1,7)))
        assert_allclose([r['correlation'] for r in data['rows']],rho[1:],atol=1e-13);self.assertAlmostEqual(data['rows'][-1]['Q'],q);self.assertAlmostEqual(data['rows'][-1]['p_value'],stats.chi2.sf(q,4));self.assertIsNone(data['rows'][1]['p_value']);self.assertAlmostEqual(data['signals'][0].metadata['time_start_s'],3.1)

    def test_recursive_forecast_and_intervals_against_closed_ar1(self):
        from signallab_pc.spectral_measurements import quantity
        source=Signal([0,1,-1,2,-2,10],5,metadata={'sample_rate_hz':10.,'time_start_s':2.});row=ar.fit(source,0)
        row.update(order=1,phi=[.5],a=[1,-.5],center_scaled=0.,offset_scaled=0.,innovation_variance=quantity(math.log(2)),near_exact=False)
        result=ar.forecast(source,row,4);expected=10*.5**np.arange(1,5);width=stats.norm.isf(.025)*np.sqrt(2*np.cumsum(.25**np.arange(4)))
        assert_allclose(result['signals'][0].values,expected);assert_allclose(result['signals'][1].values,expected-width);assert_allclose(result['signals'][2].values,expected+width);self.assertEqual(result['signals'][0].origin,11);self.assertAlmostEqual(result['signals'][0].metadata['time_start_s'],2.6)

    def test_tiny_scale_is_not_silently_converted_to_zero_noise(self):
        source=Signal(1e-250*np.random.default_rng(19).normal(size=40));row=ar.fit(source,0)
        self.assertIsNone(row['residual_mse']['value']);self.assertIsNotNone(row['residual_mse']['log_value']);self.assertTrue(math.isfinite(row['aic']));result=ar.forecast(source,row,3);self.assertEqual(len(result['signals']),3);self.assertTrue(np.all(result['signals'][2].values.real>result['signals'][0].values.real))

    def test_nonstationary_or_degenerate_fit_is_not_misrepresented_as_stationary(self):
        source=Signal(1.2**np.arange(30));row=ar.fit(source,1);self.assertFalse(row['stationary']);self.assertTrue(row['near_exact']);self.assertIn('no es estable',ar.report(row))
        self.assertIsNone(row['aic']);self.assertEqual(len(ar.forecast(source,row,3)['signals']),1)

    def test_extreme_reserved_scale_cannot_erase_training_fit(self):
        training=1e-250*np.random.default_rng(2).normal(size=40);source=Signal(np.r_[training,1e250,1e250]);row=ar.fit(source,1,validation=2);reference=ar.fit(Signal(training),1)
        self.assertEqual(row['a'],reference['a']);self.assertIsNone(row['validation_mse']);self.assertIsNotNone(row['validation_notice']);json.dumps(row,allow_nan=False)
        diagnostic=ar.diagnostics(source,row,5);self.assertEqual(len(diagnostic['signals'][0].values),39);self.assertEqual(len(diagnostic['rows']),5)


class Interface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        from test_workflow_contracts import Host
        from signallab_pc.ar_estimation_panel import ARFitPanel
        self.host=Host();self.panel=ARFitPanel(self.host);self.errors=[];self.warning=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.errors.append(str(a[2])));self.warning.start()
        self.panel.source.set_source(Signal(np.random.default_rng(30).normal(size=120),metadata={'sample_rate_hz':100.,'time_start_s':2.}))
    def tearDown(self):
        self.warning.stop();self.panel.close();self.panel.deleteLater();self.host.bar.deleteLater();self.app.processEvents()
    def test_comparison_selection_cas_payload_and_edited_form_snapshot(self):
        from signallab_pc.cas_transfer import payload
        from signallab_pc.cas_import import import_result
        self.panel.mode.setCurrentIndex(1);self.panel.maximum.setText('4');self.panel.reserve.setText('20');self.panel.calculate();self.assertFalse(self.errors)
        self.assertEqual(len(self.panel.order_rows.rows),5);self.assertIsNotNone(self.panel.result);self.assertEqual(self.panel.curves[0][0].name,'x');self.assertEqual(len(self.panel.keys[0]),2)
        record=self.host.project.get(self.panel.view.result_ids[0]);converted=payload(record,self.host);self.assertTrue(import_result(dict(payload=converted,cell=1))['encoded_value'])
        self.panel.source.expression.setText('123');self.panel.horizon.setText('99');self.panel.choose_order(3);self.assertFalse(self.errors);self.assertEqual(self.panel.result['fit']['order'],3)
        forecast=next(s for s in self.panel.result['signals'] if s.metadata.get('operation')=='ar_forecast');self.assertEqual(len(forecast.values),16);self.assertIn('anterior',self.panel.state.text())
    def test_optional_plot_and_forecast_inputs_do_not_erase_primary_fit(self):
        self.panel.method.setCurrentIndex(1);self.panel.points.setText('mal');self.panel.horizon.setText('mal');self.panel.lag.setText('mal');self.panel.calculate()
        self.assertFalse(self.errors);self.assertIsNotNone(self.panel.result['system']);self.assertEqual(self.panel.result['signals'],[]);self.assertIn('conserva',self.panel.result['report'])
    def test_failed_order_clears_previous_actions_and_csv_has_interpretation(self):
        self.panel.source.set_source(Signal(np.ones(50)));self.panel.mode.setCurrentIndex(1);self.panel.maximum.setText('3');self.panel.calculate();self.assertFalse(self.errors);self.assertIsNone(self.panel.result)
        self.panel.choose_order(0);self.assertIsNotNone(self.panel.actions.system);self.panel.choose_order(1);self.assertIsNone(self.panel.actions.system);self.assertIsNone(self.panel.output.result)
        self.assertFalse(self.panel.tabs.isHidden());self.panel.choose_order(0);self.assertIsNotNone(self.panel.actions.system)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'orders.csv'
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(str(path),'CSV')):self.panel.export('orders')
            with path.open(encoding='utf-8') as stream:meta=json.loads(stream.readline()[2:]);rows=list(csv.DictReader(stream))
            self.assertIn('mismas respuestas',meta['scope']);self.assertEqual(len(rows),4);self.assertTrue(rows[1]['error'])

    def test_stationary_generation_is_preserved_and_reproducible(self):
        self.panel.order.setText('0');self.panel.generate.setChecked(True);self.panel.count.setText('12');self.panel.calculate();self.assertFalse(self.errors)
        first=next(s for s in self.panel.result['signals'] if s.metadata.get('operation')=='stationary_arma_realization');self.assertEqual(first.metadata['sample_rate_hz'],100)
        self.panel.calculate();self.assertFalse(self.errors);second=next(s for s in self.panel.result['signals'] if s.metadata.get('operation')=='stationary_arma_realization');assert_allclose(first.values,second.values)


if __name__=='__main__':unittest.main()
