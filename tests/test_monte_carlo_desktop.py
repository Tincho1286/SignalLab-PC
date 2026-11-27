from pathlib import Path

import numpy as np

from signallab_pc.model import Signal
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class MonteCarloWorkbenchTests(DesktopSessionFixture):
    def test_default_campaign_opens_its_convergence_plot_from_results(self):
        window = self.window()
        window.show()
        route = ROUTES['statistical_experiment','campaign']
        window.open_tool(route)
        page = window.pages[route]
        panel = page.panel
        launcher = page.workspace.results.graph_launcher
        self.assertFalse(launcher.isEnabled())

        window.calculate_active()
        self.assertIs(page.workspace.input_issue.field(), panel.directory)
        self.assertFalse(panel.seed.text())
        self.assertIsNone(panel.campaign)

        panel.directory.setText(str(self.path/'default-campaign'))
        window.calculate_active()
        self.wait_for_calculation(window, timeout_ms=12000)
        self.warning.assert_not_called()
        self.assertEqual(len(panel.campaign.replicas), 128)
        self.assertTrue(launcher.isEnabled())
        launcher.click()
        self.assertTrue(panel.canvas._signallab_window.isVisible())
        line, = panel.figure.axes[0].lines
        self.assertEqual(line.get_xdata()[-1], 128)

    def test_parameter_sweep_displays_same_replica_axis_and_persists_summary(self):
        window = self.window()
        route = ROUTES['statistical_experiment','campaign']
        window.open_tool(route)
        panel = window.pages[route].panel
        panel.directory.setText(str(Path(self.path)/'campaign'))
        panel.replicas.setText('8')
        panel.samples.setText('16')
        panel.seed.setText('3')
        panel.batch.setText('4')
        panel.axis.setCurrentIndex(panel.axis.findData('mean'))
        panel.axis_values.setText('0, 3')
        panel.common.setChecked(True)
        window.calculate_active()
        self.wait_for_calculation(window)
        self.warning.assert_not_called()
        record = next(row for row in window.project.headers('calculation') if row['title']=='Campaña de Monte Carlo')
        result = window.project.get(record['id'])
        self.assertAlmostEqual(result['differences'][0]['value'],3.)
        self.assertEqual(result['replicas'],8)
        self.assertTrue(panel.export_button.isEnabled())
        self.assertFalse(panel.resume_button.isEnabled())
        first, second = panel.figure.axes[0].lines
        np.testing.assert_array_equal(first.get_xdata(),second.get_xdata())
        np.testing.assert_allclose(second.get_ydata()-first.get_ydata(),3.)

    def test_bootstrap_preserves_project_source_and_renders_distribution(self):
        window = self.window()
        window.show()
        route = ROUTES['statistical_experiment','bootstrap']
        source = Signal([-2,1,2,7,8],origin=-3)
        parent = window.publish(source)
        window.send_signal(source,parent,route)
        page = window.pages[route]
        panel = page.panel
        launcher = page.workspace.results.graph_launcher
        self.assertFalse(launcher.isEnabled())
        panel.seed.setText('5')
        panel.replicas.setText('32')
        panel.block.setText('2')
        window.calculate_active()
        self.wait_for_calculation(window)
        self.warning.assert_not_called()
        result = next(row for row in window.project.headers('calculation') if row['operation']=='Incertidumbre por bootstrap')
        self.assertEqual(result['parents'],[parent])
        self.assertEqual(window.project.get(result['id'])['block_length'],2)
        self.assertIn('Intervalo percentil',panel.report.toPlainText())
        self.assertTrue(panel.tabs.isTabVisible(1))
        self.assertTrue(launcher.isEnabled())
        launcher.click()
        self.assertTrue(panel.canvas._signallab_window.isVisible())
        axes, = panel.figure.axes
        self.assertEqual(axes.get_ylabel(), 'Réplicas')
        self.assertEqual(sum(bar.get_height() for bar in axes.patches), 32)
