"""Exercise the original Workbench realization route with the expanded engine."""

from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic, sleep
from unittest.mock import patch

import numpy as np

from signallab_pc.jobs import checkpoint
from signallab_pc.model import Signal
from signallab_pc.probability import Distribution, generate_realizations
from signallab_pc.session import load
from signallab_pc.session_fields import field_values
from signallab_pc.statistical_inference import fit_distribution, infer_record
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class ProbabilityWorkbenchTests(DesktopSessionFixture):
    def open_generators(self):
        window = self.window()
        route = ROUTES['random', 'generate']
        window.open_tool(route)
        return window, window.pages[route].panel

    def test_poisson_replicas_share_python_results_and_preserve_session(self):
        window, panel = self.open_generators()
        self.assertEqual([panel.distribution.itemData(i) for i in range(3)],
                         ['gaussian', 'uniform', 'bernoulli'])
        panel.distribution.setCurrentIndex(panel.distribution.findData('poisson'))
        self.assertTrue(panel.replicas.isHidden())
        panel.advanced.setChecked(True)
        self.assertFalse(panel.replicas.isHidden())
        panel.fields['poisson.rate'].setText('3/2')
        panel.count.setText('24')
        panel.replicas.setText('2')
        panel.seed.setText('19')
        panel.origin.setText('-7')
        panel.sample_rate.setText('600')
        window.calculate_active()
        self.wait_for_calculation(window)
        expected = generate_realizations(Distribution('poisson', {'rate': 1.5}),
                                         24, 19, replicas=2, origin=-7, rate=600)
        outputs = {window.project.get(row['id']).metadata['substream'][0]: row
                   for row in window.project.headers() if row['operation'] == 'Generar realización'}
        self.assertEqual(len(outputs), 2)
        for index, signal in enumerate(expected):
            row = outputs[index]
            actual = window.project.get(row['id'])
            np.testing.assert_array_equal(actual.values, signal.values)
            self.assertEqual(actual.metadata, signal.metadata)
            self.assertEqual(actual.origin, -7)
            parent, = row['parents']
            self.assertEqual(window.project.get(parent)['parameters'], {'rate': 1.5})
        self.assertEqual(panel.sample_choice.count(), 2)
        panel.sample_choice.setCurrentIndex(1)
        self.assertIn('600', panel.report.toPlainText())
        self.assertEqual(field_values(panel, set())['fields.poisson.rate'], '3/2')

        with TemporaryDirectory() as folder:
            path = Path(folder) / 'probability.slproj'
            window.project.save(path)
            recovered, _ = load(path)
            np.testing.assert_array_equal(recovered.get(outputs[1]['id']).values, expected[1].values)

        panel.method.setCurrentIndex(panel.method.findData('cdf'))
        panel.argument.setText('1')
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertIn('Probabilidad acumulada', panel.report.toPlainText())
        self.assertTrue(panel.replicas.isHidden())

    def test_cancel_generated_batch_leaves_the_project_untouched(self):
        window, panel = self.open_generators()
        panel.distribution.setCurrentIndex(panel.distribution.findData('poisson'))
        before = window.project.headers()
        started = Event()

        def interrupted(*_, **__):
            started.set()
            deadline = monotonic() + 4
            while monotonic() < deadline:
                checkpoint()
                sleep(.005)
            raise AssertionError('El cálculo de prueba no recibió cancelación.')

        with patch('signallab_pc.random_panel.generate_realizations', interrupted):
            window.calculate_active()
            deadline = monotonic() + 4
            while not started.is_set() and monotonic() < deadline:
                self.app.processEvents()
                sleep(.005)
            self.assertTrue(started.is_set())
            window._cancel_operations()
            self.wait_for_calculation(window)

        self.assertEqual(window.project.headers(), before)
        self.assertEqual(panel.sample_choice.count(), 0)

    def test_descriptive_figures_follow_the_same_saved_calculation(self):
        window = self.window()
        route = ROUTES['random', 'statistics']
        source = Signal([1, 1, 2, 3, 100], name='Registro de prueba')
        origin = window.publish(source, operation='Entrada')
        window.send_signal(source, origin, route)
        panel = window.pages[route].panel
        panel.diagnostics.setChecked(True)
        panel.reference_normal.setChecked(True)
        window.calculate_active()
        self.wait_for_calculation(window)
        row = next(record for record in window.project.headers()
                   if record['operation'] == 'Estadísticas de registro')
        report = window.project.get(row['id'])['descriptive']
        self.assertEqual(report['boxplot']['outliers'], 1)
        self.assertIn('Mediana: 2', panel.report.toPlainText())
        for key in ('cdf','survival','boxplot','qq'):
            panel.plot_kind.setCurrentIndex(panel.plot_kind.findData(key))
            self.assertEqual(len(panel.figure.axes), 1)
        qq = panel.figure.axes[0].collections[0].get_offsets()
        self.assertEqual(len(qq), len(source.values))

    def test_two_sample_inference_and_fit_share_api_results(self):
        window = self.window()
        route = ROUTES['random', 'statistics']
        first, second = Signal([1,2,3], origin=-1), Signal([-1,0,1], origin=2)
        first_id, second_id = [window.publish(source, operation='Entrada') for source in (first,second)]
        window.send_signal(first, first_id, route)
        panel = window.pages[route].panel
        self.assertTrue(panel.second_source.isHidden())
        panel.analysis.setCurrentIndex(panel.analysis.findData('infer'))
        panel.inference_method.setCurrentIndex(panel.inference_method.findData('welch'))
        self.assertFalse(panel.second_source.isHidden())
        panel.second_source.set_source(window.project.get(second_id), second_id)
        panel.iid.setChecked(True)
        panel.null_value.setText('0')
        window.calculate_active()
        self.wait_for_calculation(window)
        row = window.project.headers()[-1]
        self.assertEqual(row['parents'], [first_id, second_id])
        self.assertEqual(window.project.get(row['id']), infer_record(first, 'welch', iid=True, null=0, second=second))
        self.assertIn('Intervalo bilateral', panel.report.toPlainText())
        self.assertFalse(panel.tabs.isTabEnabled(2))
        panel.analysis.setCurrentIndex(panel.analysis.findData('fit'))
        self.assertTrue(panel.second_source.isHidden())
        panel.fit_interval.setChecked(True)
        window.calculate_active()
        self.wait_for_calculation(window)
        row = window.project.headers()[-1]
        self.assertEqual(window.project.get(row['id']), fit_distribution(first, 'normal', level=.95, iid=True))
        self.assertEqual(row['parents'], [first_id])
        self.assertIn('Intervalos bilaterales', panel.report.toPlainText())
        panel.analysis.setCurrentIndex(panel.analysis.findData('describe'))
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertTrue(panel.tabs.isTabEnabled(2))
        self.assertEqual(panel.plot_kind.currentData(), 'histogram')
