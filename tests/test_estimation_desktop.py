import numpy as np

from signallab_pc.state_space import StateModel
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture
from test_optimal_estimation import matched_records


class EstimationWorkbenchTests(DesktopSessionFixture):
    def test_gaussian_measurement_design_retains_prior_and_reports_cramer_rao(self):
        window = self.window()
        route = ROUTES['estimation','gaussian']
        window.open_tool(route)
        panel = window.pages[route].panel
        panel.data.setText('3, 1')
        panel.design.setText('1; 2')
        panel.noise.setText('2, 1; 1, 3')
        panel.prior.setText('2')
        panel.prior_covariance.setText('4')
        window.calculate_active()
        self.wait_for_calculation(window)
        report = window.project.get(window.project.headers('calculation')[-1]['id'])
        self.assertAlmostEqual(report['posterior']['map'][0], 34/33)
        self.assertIn('Cramér–Rao', panel.report.toPlainText())
        panel.design.setText('1; 3')
        self.assertTrue(panel.state.property('resultStale'))

    def test_wiener_reuses_records_and_exposes_model_and_aligned_graph(self):
        window = self.window()
        route = ROUTES['estimation','wiener']
        window.open_tool(route)
        panel = window.pages[route].panel
        x,d,h,_ = matched_records()
        first, second = window.publish(x), window.publish(d)
        panel.observed.set_source(window.project.get(first), first)
        panel.desired.set_source(window.project.get(second), second)
        panel.length.setText('2')
        panel.reserve.setText('3')
        panel.offset.setChecked(True)
        window.calculate_active()
        self.wait_for_calculation(window)
        records = window.project.headers('system')
        np.testing.assert_allclose(window.project.get(records[-1]['id']).b, h, atol=2e-14)
        for curve in panel.output.displayed_signals():
            self.assertEqual(curve.origin, -2)
            self.assertEqual(curve.metadata['time_start_s'], 2.25)
        self.assertTrue(panel.actions.reuse.isEnabled())
        self.assertIn('fuera del entrenamiento', panel.report.toPlainText())
        panel.mode.setCurrentIndex(1)
        panel.autocorrelation.setText('2, 1')
        panel.cross.setText('1, 1')
        panel.power.setText('1')
        window.calculate_active()
        self.wait_for_calculation(window)
        report = window.project.get(window.project.headers('calculation')[-1]['id'])
        np.testing.assert_allclose(report['coefficients']['real'], [1/3,1/3], atol=2e-14)
        self.assertAlmostEqual(report['theoretical_mse']['value'], 1/3)
        self.assertFalse(panel.tabs.isTabVisible(1))

    def test_kalman_reuses_a_discrete_model_and_shows_prediction_when_measurement_missing(self):
        window = self.window()
        route = ROUTES['estimation','kalman']
        model = StateModel([[1]],[[0]],[[1]],[[0]],.5,name='Constante medida')
        parent = window.publish(model)
        window.send_model(model,parent,route)
        panel = window.pages[route].panel
        panel.origin.setText('-6')
        panel.initial.setText('0')
        for name,text in [('Q','0'),('R','1'),('P','1'),('y','2; 100; 10'),('mask','1; 0; 1')]:
            panel.matrices[name].setText(text)
        window.calculate_active()
        self.wait_for_calculation(window)
        self.warning.assert_not_called()
        report = next(header for header in window.project.headers('calculation') if header['operation']=='Estimar estados')
        self.assertEqual(report['parents'],[parent])
        self.assertEqual(window.project.get(report['id'])['prediction_only_steps'],1)
        prior, updated = panel.output.displayed_signals()
        np.testing.assert_allclose(prior.values,[0,1,1])
        np.testing.assert_allclose(updated.values,[1,1,4])
        self.assertEqual((updated.origin,updated.metadata['time_start_s']),(-6,-3.))
        panel.selector.setCurrentIndex(1)
        np.testing.assert_allclose(panel.output.displayed_signals()[0].values,[.5,.5,1/3])
        self.assertIn('Última corrección disponible',panel.report.toPlainText())
