import numpy as np
from numpy.testing import assert_allclose

from signallab_pc.rf_storage import load_network
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class RFWorkbenchTests(DesktopSessionFixture):
    def panel(self,window,task):
        route=ROUTES['rf',task]
        window.open_tool(route)
        return window.pages[route].panel

    def test_rf_network_definition_publishes_and_reuses_the_result(self):
        window=self.window()
        panel=self.panel(window,'network')
        panel.mode.setCurrentIndex(panel.mode.findData('define'))
        for key,value in (('frequencies','1e6,3e6'),('matrix','0,0.02,0.7,0;0,0.01,0.5,0'),('reference','50,75')):
            panel.editors[key].setText(value)
        panel.calculate()
        self.wait_for_calculation(window)
        net=load_network(window.project,panel.active_record)
        assert_allclose(net.values[:,1,0],[.7,.5])
        self.assertTrue(panel.canvas._signallab_has_plot_result)
        previous=panel.active_record
        panel.mode.setCurrentIndex(panel.mode.findData('renormalize'))
        panel._set_input(0,net.name,previous)
        panel.editors['reference'].setText('50')
        panel.calculate()
        self.wait_for_calculation(window)
        self.assertNotEqual(previous,panel.active_record)
        assert_allclose(load_network(window.project,panel.active_record).reference_ohm,50)
        self.assertIn('Frecuencias',panel.report.toPlainText())
        result=panel.active_record
        window.focus_result(result)
        self.assertTrue(window.reuse_selection.isEnabled())
        self.assertIn('Huella de matrices',window.project_details.toPlainText())
        window.prepare_selected_reuse()
        next(action for action in window.reuse_actions if 'Analizar' in action.text()).trigger()
        self.assertEqual(panel.inputs[0][1],result)
        self.assertEqual(panel.mode.currentData(),'analyze')

    def test_matching_chart_contains_smith_grid_and_reflection_marker(self):
        window=self.window()
        panel=self.panel(window,'line')
        panel.mode.setCurrentIndex(panel.mode.findData('match'))
        panel.editors['method'].setCurrentIndex(panel.editors['method'].findData('quarter_wave'))
        panel.editors['load'].setText('100')
        panel.calculate()
        self.wait_for_calculation(window)
        self.assertIn('Longitud de línea',panel.report.toPlainText())
        panel.figure_choice.setCurrentIndex(panel.figure_choice.findData('admittance'))
        axis,f,gamma,marker=panel._smith
        at=np.flatnonzero(f==1e9)[0]
        assert_allclose(gamma[at],0,atol=1e-15)
        from types import SimpleNamespace
        panel._mark_smith(SimpleNamespace(inaxes=axis,button=1,xdata=gamma[at].real,ydata=gamma[at].imag))
        self.assertIn('Hz',panel._smith[-1].get_text())

    def test_zoom_preserves_origin_and_bessel_control_is_contextual(self):
        window=self.window()
        panel=self.panel(window,'spectral')
        panel.source.expression.setText('1+n')
        panel.source.origin.setText('-2')
        panel.source.count.setText('3')
        panel.editors['count'].setText('21')
        panel.calculate()
        self.wait_for_calculation(window)
        value=window.project.get(panel.active_record)
        expected=np.exp(-1j*np.outer(value.axis,[-2,-1,0])) @ [-1,0,1]
        assert_allclose(value.values,expected,atol=1e-14)
        route=ROUTES['course_tools','analog']
        window.open_tool(route)
        designer=window.pages[route].panel
        method=designer.fields['method']
        method.setCurrentIndex(method.findData('bessel_prototype'))
        self.assertTrue(designer.band_edges.isHidden())
        designer.fields['bessel_norm'].setCurrentIndex(designer.fields['bessel_norm'].findData('delay'))
        designer.calculate()
        self.wait_for_calculation(window)
        self.assertIn('Bessel',designer.report.toPlainText())

    def test_library_has_context_for_every_rf_tool(self):
        from signallab_pc.library_catalog import sections
        from signallab_pc.visual_help import diagrams_for
        for task in ('network','line','link','spectral'):
            article=next(a for a in sections() if a['article_id']==f'tool:rf:{task}')
            self.assertGreaterEqual(len(article['blocks']),4)
            self.assertTrue(diagrams_for(article))

    def test_link_uncertainty_publishes_report_and_convergence(self):
        window=self.window()
        panel=self.panel(window,'link')
        panel.mode.setCurrentIndex(panel.mode.findData('link_campaign'))
        panel.editors['replicas'].setText('8')
        panel.editors['directory'].setText(str(self.path/'rf'))
        panel.calculate()
        self.wait_for_calculation(window)
        self.assertTrue(panel.canvas._signallab_has_plot_result)
        self.assertEqual(panel.active_result.data.report['replicas'],8)
        self.assertTrue((self.path/'rf'/'monte-carlo.json').is_file())
        saved=window.project.get(panel.active_record)
        self.assertEqual(len(saved['replicate_summaries']),8)

    def test_sensitivity_views_use_same_result_as_python(self):
        window=self.window()
        panel=self.panel(window,'line')
        panel.mode.setCurrentIndex(panel.mode.findData('matching_sweep'))
        panel.editors['method'].setCurrentIndex(panel.editors['method'].findData('quarter_wave'))
        panel.editors['load'].setText('100')
        panel.editors['minimum'].setText('1e9')
        panel.editors['maximum'].setText('2e9')
        panel.editors['points'].setText('2')
        panel.calculate()
        self.wait_for_calculation(window)
        data=panel.active_result.data
        assert_allclose(data.reflection[:,0],(100-data.values)/(100+data.values),atol=1e-15)
        self.assertIn('mayor',panel.report.toPlainText())
        link=self.panel(window,'link')
        link.mode.setCurrentIndex(link.mode.findData('noise_sweep'))
        link.calculate()
        self.wait_for_calculation(window)
        self.assertEqual(len(link.active_result.data['noise']),3)
        self.assertTrue(link.canvas._signallab_has_plot_result)
