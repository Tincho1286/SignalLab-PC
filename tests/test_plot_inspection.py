"""Full curve data, sampled extrema, cursor editing and stable report scrolling."""
import os,time,json,csv,tempfile,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout
from signallab_pc.model import Signal
from signallab_pc.filters import Transfer
from signallab_pc.signal_plot import plot_samples,configure_signal_axis
from signallab_pc.probe_data import collect
from signallab_pc import plot_inspection as inspection


class Samples(unittest.TestCase):
    def trace(self,x,y,source=None,component='real'):
        figure=Figure();axis=figure.add_subplot(111);plot_samples(axis,x,y,discrete=source is not None and source.domain=='discrete',source=source,component=component,label='x')
        return collect(figure)[0]
    def test_full_source_extrema_are_not_the_decimated_visible_subset(self):
        source=Signal([0,2,0,9,0,1,0],-3,expression='sin(n)');trace=self.trace(source.axis[::2],source.values.real[::2],source)
        result=inspection.extrema(trace,local=True);self.assertTrue(result['complete']);self.assertEqual(result['rows'][0]['x'],0);self.assertEqual(result['rows'][0]['y'],9);self.assertTrue(any(r['x']==-2 for r in result['rows']))
    def test_nonfinite_gaps_and_plateaus_are_not_bridged(self):
        trace=self.trace(np.arange(9),[0,2,2,0,np.nan,3,2,4,0]);rows=inspection.extrema(trace,local=True)['rows'];self.assertTrue(any(r['plateau']==2 for r in rows));self.assertFalse(any(r['index']==5 for r in rows if r['kind']=='Máximo local'))
        with self.assertRaises(ValueError):inspection.extrema(trace,low=20)
        with self.assertRaises(ValueError):inspection.extrema(SimpleNamespace(spatial=True))
    def test_large_integer_indices_and_adjacent_navigation_remain_exact(self):
        origin=2**60;source=Signal([1,3,0,2],origin);trace=self.trace(source.axis,source.values.real,source)
        self.assertEqual(inspection.extrema(trace)['rows'][0]['x'],origin+1);self.assertEqual(inspection.nearest(trace,origin+2)[1],origin+2);self.assertEqual(inspection.adjacent(trace,origin+2,1),origin+3)
        inspection.stored_curve(trace.artist,source.axis,source.values.real,source,'real');self.assertEqual(trace.point(2.1)[0],origin+2)
    def test_principal_phase_jump_does_not_invent_an_interior_peak(self):
        phase=np.array([0,1,2,3,-3,-2,-1]);source=Signal(np.exp(1j*phase),0,1,'rad/muestra','X','frequency');trace=self.trace(source.axis,phase,source,'phase');rows=inspection.extrema(trace,local=True)['rows'];self.assertEqual(len(rows),2)
    def test_editing_values_invalidates_old_formula_but_copying_does_not(self):
        source=Signal([0,1,2],expression='n');self.assertEqual(source.copy_with(name='renamed').expression,'n');self.assertEqual(source.copy_with(values=source.values.copy()).expression,'n');self.assertEqual(source.copy_with(values=[1,2,3]).expression,'');self.assertEqual(source.copy_with(values=[1,2,3],expression='n+1').expression,'n+1')
        self.assertEqual(source.copy_with(origin=10).expression,'')
        changed=source.copy_with(values=[1,2,3]);self.assertIn('no una fórmula',inspection.definition(self.trace(changed.axis,changed.values.real,changed)).plain_text())
    def test_transfer_definitions_cover_both_domains_and_extra_advance(self):
        for domain in ('digital','analog'):
            system=Transfer([1],[1,.5],domain=domain);trace=self.trace([0,1],[1,.5]);inspection.system_curve(trace.artist,system,'delay',advance=2 if domain=='digital' else 0);text=inspection.definition(trace).plain_text()
            self.assertIn('H(z)' if domain=='digital' else 'H(s)',text);self.assertIn('diff(F(w),w)',text)
            if domain=='digital':self.assertIn('exp(i*w*(2))',text)
    def test_stored_formula_component_and_conditions_are_explicit(self):
        source=Signal([1,2],0,1,'rad/muestra','F','frequency','1/(1+w)',{'source_frequency_condition':'w != -1'});trace=self.trace(source.axis,source.values.real,source);text=inspection.definition(trace).plain_text();self.assertIn('1/(1+w)',text.replace(' ',''));self.assertIn('re(f(w))',text);self.assertIn('w != -1',text)

    def test_temporal_inverse_and_window_formulas_are_used_only_for_matching_data(self):
        from signallab_pc.temporal_formula import attach_temporal_formula
        from signallab_pc.window_signals import generate_window
        source=Signal([1,.5,.25],metadata={'operation':'inverse_dtft_expression_samples'});attach_temporal_formula(source,dict(evaluated=True,result='(1/2)^n',scope='n>=0'));text=inspection.definition(self.trace(source.axis,source.values.real,source)).plain_text();self.assertIn('(1/2)^n',text)
        window=generate_window('hann',9,-4);text=inspection.definition(self.trace(window.axis,window.values.real,window)).plain_text();self.assertIn('w[n]',text);self.assertIn('cos',text)
        changed=window.copy_with(values=np.ones(9));text=inspection.definition(self.trace(changed.axis,changed.values.real,changed)).plain_text();self.assertIn('no una fórmula',text)

    def test_sampled_continuous_formula_retains_the_time_mapping(self):
        from signallab_pc.sampling import sample_expression
        source=sample_expression('cos(2*pi*t)',.25,8,8);text=inspection.definition(self.trace(source.axis,source.values.real,source)).plain_text();self.assertIn('g(t)',text);self.assertIn('f[n]',text);self.assertIn('cos(2 * pi * t)',text);self.assertIn('(0.25)',text);self.assertIn('(8.0)',text)


class Interaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        from signallab_pc.plot_probe import PlotProbe
        self.widget=QWidget();layout=QVBoxLayout(self.widget);self.figure=Figure();self.canvas=FigureCanvasQTAgg(self.figure);layout.addWidget(self.canvas);self.toolbar=NavigationToolbar2QT(self.canvas,self.widget);self.axis=self.figure.add_subplot(111);self.source=Signal([0,1,0,-1,0],-2,expression='-sin(pi*n/2)');plot_samples(self.axis,self.source.axis,self.source.values.real,discrete=True,source=self.source,component='real',label='x');configure_signal_axis(self.axis,self.source);self.probe=PlotProbe(self.canvas,self.toolbar,layout);self.canvas._signallab_window=self.widget;self.widget.resize(900,650);self.widget.show();self.canvas.draw();self.app.processEvents();self.trace=self.probe.traces[0]
    def tearDown(self):
        if self.probe.inspector is not None:self.probe.inspector.close()
        self.widget.close();self.widget.deleteLater();self.app.processEvents()
    def test_precise_cursor_position_and_keyboard_keep_other_cursor(self):
        self.probe.focus(self.trace,-1,'a');self.probe.focus(self.trace,1,'b');saved=dict(self.probe.b);self.probe.focus(self.trace,0,'a');self.assertEqual(self.probe.b,saved);self.assertEqual(self.probe.a[self.trace.key][0],0);self.probe.key(SimpleNamespace(key='right'));self.assertEqual(self.probe.b[self.trace.key][0],2)
        self.probe.clear()
        with self.assertRaises(ValueError):self.probe.focus(self.trace,0,'b')
    def test_dragging_a_cursor_preserves_b_and_snaps_to_discrete_points(self):
        self.probe.focus(self.trace,-1,'a');self.probe.focus(self.trace,1,'b');saved=dict(self.probe.b);x,y=self.axis.transData.transform((-1,1));press=MouseEvent('button_press_event',self.canvas,x,y,button=1);self.probe.press(press);self.assertEqual(self.probe._dragging,'a')
        x,y=self.axis.transData.transform((.2,0));self.probe.motion(MouseEvent('motion_notify_event',self.canvas,x,y,button=1),force=True);self.probe.release(None);self.assertEqual(self.probe.a[self.trace.key][0],0);self.assertEqual(self.probe.b,saved)
    def test_design_editor_clicks_are_not_taken_by_cursor_dragging(self):
        self.canvas._signallab_editable=True;self.probe.focus(self.trace,-1,'a');x,y=self.axis.transData.transform((-1,1));self.probe.press(MouseEvent('button_press_event',self.canvas,x,y,button=1));self.assertIsNone(self.probe._dragging)
    def test_inspector_search_pin_export_and_redraw_invalidation(self):
        self.probe.open_inspector();dialog=self.probe.inspector;dialog.scope.setCurrentIndex(1);dialog.find();self.assertEqual(dialog.model.rows[0]['x'],-1);dialog.table.selectRow(0);dialog.use_point('a');self.assertEqual(self.probe.a[self.trace.key][0],-1)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'extrema.csv'
            with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',return_value=(str(path),'CSV')):dialog.save()
            with path.open(encoding='utf-8') as stream:meta=json.loads(stream.readline()[2:]);rows=list(csv.DictReader(stream))
            self.assertIn('puntos finitos',meta['scope']);self.assertEqual(float(rows[0]['y']),1)
        self.axis.clear();self.axis.plot([0,1],[2,3]);self.canvas.draw();self.assertIsNone(dialog.result);self.assertEqual(dialog.model.rows,[])
    def test_inspector_direct_reading_accepts_expressions_and_steps(self):
        self.probe.open_inspector();dialog=self.probe.inspector;dialog.coordinate.setText('2-3');dialog.locate();self.assertEqual(self.probe.live[self.trace.key][0],-1);dialog.step(1);self.assertEqual(self.probe.live[self.trace.key][0],0)

    def test_scientific_controls_wrap_without_losing_widgets_or_actions(self):
        from PySide6.QtWidgets import QComboBox
        from signallab_pc.figure_controls import ScientificControls
        combo=QComboBox();combo.addItems(['Módulo y fase','Parte real e imaginaria']);self.toolbar.addWidget(combo);controls=ScientificControls(self.toolbar,self.widget);self.widget.layout().insertWidget(0,controls);self.widget.resize(620,650);self.app.processEvents();combo.setCurrentIndex(1);self.assertEqual(combo.currentText(),'Parte real e imaginaria')
        self.assertNotIn(self.probe.inspect_action,self.toolbar.actions());self.assertTrue(any(action is self.probe.inspect_action and not widget.isHidden() for action,widget in controls.projected))
        for action,widget in controls.projected:
            if action.isVisible():self.assertGreaterEqual(widget.geometry().left(),0);self.assertLessEqual(widget.geometry().right(),controls.width())
        self.probe.action.setChecked(False);button=next(w for a,w in controls.projected if a is self.probe.action);self.assertFalse(button.isChecked());self.assertFalse(self.probe.enabled)


class Reports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def wait(self):
        end=time.monotonic()+.16
        while time.monotonic()<end:self.app.processEvents();time.sleep(.005)
    def report(self):
        from signallab_pc.transfer_report import TransferResultReport
        from signallab_pc.result_summary import Summary,Section,Formula
        report=TransferResultReport();report.resize(550,260);report.show();report.set_readable(Summary('Informe',[Section('Sección '+str(i),formulas=[Formula('H(z) = (1+2*z^(-1))/(1-0.5*z^(-1))','H')],paragraphs=['Explicación del sistema y sus condiciones. '*5]) for i in range(12)]));self.wait();self.addCleanup(report.close);return report
    def test_scrolling_does_not_regenerate_or_jump_the_report(self):
        report=self.report();revision=report._report_revision;bar=report.verticalScrollBar()
        for fraction in (.2,.5,.8,.95):
            target=round(bar.maximum()*fraction);bar.setValue(target);self.wait();self.assertEqual(report._report_revision,revision);self.assertLessEqual(abs(bar.value()-target),1)
    def test_resizing_preserves_visible_text_and_clear_does_not_revive_summary(self):
        report=self.report();bar=report.verticalScrollBar();bar.setValue(bar.maximum()//2);before=report.cursorForPosition(__import__('PySide6.QtCore',fromlist=['QPoint']).QPoint(0,0)).block().text();report.resize(700,260);self.wait();after=report.cursorForPosition(__import__('PySide6.QtCore',fromlist=['QPoint']).QPoint(0,0)).block().text();self.assertEqual(before,after)
        report.setPlainText('Sin resultado');report.resize(450,260);self.wait();self.assertEqual(report.toPlainText(),'Sin resultado');self.assertIsNone(report.summary)
    def test_frequency_tab_reopens_its_retained_canvas_after_alternatives(self):
        from signallab_pc.system_analysis_panel import SystemAnalysisPanel
        from test_workflow_contracts import Host
        host=Host();panel=SystemAnalysisPanel(host);self.addCleanup(panel.close);self.addCleanup(host.bar.close);panel.frequency_data=object()
        with patch('signallab_pc.plot_view.enlarge_plot') as show:
            panel._result_tab_changed(0);show.assert_not_called();panel._result_tab_changed(1);show.assert_called_once_with(panel.canvas,panel)


if __name__=='__main__':unittest.main()
