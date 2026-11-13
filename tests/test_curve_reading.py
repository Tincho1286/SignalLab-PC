"""Developed formula values and the real Workbench command-bar regression."""
import os,time,unittest
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from unittest.mock import patch
import numpy as np
import sympy as sp
from numpy.testing import assert_allclose
from scipy.signal import butter
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QPushButton,QDialog,QMessageBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc import curve_algebra as algebra,plot_inspection as inspect
from signallab_pc.probe_data import collect


def evaluate(parts,value,coordinate):
    w=parts[0];symbols=[];numbers=[]
    for symbol,expression in parts[4].get('definitions',[]) if len(parts)>4 else []:
        numbers.append(sp.lambdify((w,*symbols),expression,'numpy')(coordinate,*numbers));symbols.append(symbol)
    return sp.lambdify((w,*symbols),value,'numpy')(coordinate,*numbers)


class Algebra(unittest.TestCase):
    def test_analog_components_and_magnitude_equal_direct_polynomial_evaluation(self):
        system=Transfer([2+1j,3],[1,1-2j,4],domain='analog');parts=algebra.transfer_components(system);w=np.array([-.7,0,.3,2.])
        actual=np.polyval(system.b,1j*w)/np.polyval(system.a,1j*w)
        assert_allclose(evaluate(parts,parts[1],w)+1j*evaluate(parts,parts[2],w),actual)
        assert_allclose(evaluate(parts,parts[3],w),abs(actual))
    def test_digital_advance_and_factored_sos_retain_their_values(self):
        for system,extra in ((Transfer([1,2j,-.3],[1,-.7],advance=2),3),(Transfer.from_sos(butter(8,.3,output='sos')),0)):
            parts=algebra.transfer_components(system,extra);w=np.array([-.9,-.3,.4,1.4]);expected=system.response(w)*np.exp(1j*w*extra)
            assert_allclose(evaluate(parts,parts[1],w)+1j*evaluate(parts,parts[2],w),expected,atol=2e-14)
            assert_allclose(evaluate(parts,parts[3],w),abs(expected),atol=2e-14)
    def test_arctangent_preserves_all_quadrants_and_excludes_zero(self):
        r,i=sp.symbols('R I',real=True);fn=sp.lambdify((r,i),algebra.angle(r,i),'numpy')
        with np.errstate(all='ignore'):
            for real,imag in ((2,3),(-2,3),(-2,-3),(2,-3),(0,2),(0,-2),(-2,0),(2,0)):
                self.assertAlmostEqual(float(fn(np.asarray(float(real)),np.asarray(float(imag)))),np.angle(complex(real,imag)))
            self.assertTrue(np.isnan(fn(np.asarray(0.),np.asarray(0.))))
    def test_reported_second_order_and_group_delay_have_developed_formulas(self):
        system=Transfer([1],[1,1,1],domain='analog');parts=algebra.transfer_components(system,derivative=True);w=np.array([0,.5,1.,2.])
        expected=1/np.sqrt((1-w*w)**2+w*w);assert_allclose(evaluate(parts,parts[3],w),expected)
        assert_allclose(evaluate(parts,parts[4]['delay'],w),(1+w*w)/((1-w*w)**2+w*w))
        for role in ('magnitude','phase','delay'):
            report='\n'.join(f.expression for section in algebra.sections(parts,role) for f in section.formulas)
            for opaque in ('arg(', 're(', 'im(', 'F(w)'):self.assertNotIn(opaque,report)
    def test_piecewise_signal_and_complex_exponential_are_developed(self):
        for expression in ('exp(i*w)','Piecewise((1,w<0),(2,True))'):
            parts=algebra.expression_components(expression,'w');x=np.array([-.8,.4]);z=evaluate(parts,parts[1],x)+1j*evaluate(parts,parts[2],x)
            expected=np.exp(1j*x) if expression.startswith('exp') else np.where(x<0,1,2)
            assert_allclose(z,expected);self.assertFalse(parts[1].has(sp.re,sp.im,sp.arg))
        with self.assertRaises(ValueError):algebra.expression_components('a+w','w')
    def test_removable_factors_do_not_invent_holes_in_developed_curves(self):
        for system,w in ((Transfer([1,-1],[1,-1]),0.),(Transfer([1,0,1],[1,0,1],domain='analog'),1.),(Transfer.from_sos([[1,0,0,1,-1,0],[1,-1,0,1,0,0]]),0.)):
            parts=algebra.transfer_components(system,derivative=True)
            self.assertEqual(float(evaluate(parts,parts[1],w)),1);self.assertEqual(float(evaluate(parts,parts[2],w)),0);self.assertEqual(float(evaluate(parts,parts[3],w)),1)
    def test_repeated_global_extrema_and_plateaus_are_not_lost(self):
        figure=Figure();axis=figure.add_subplot();axis.plot(np.arange(8),[0,3,3,0,-2,0,3,-2]);trace=collect(figure)[0]
        result=inspect.extrema(trace,local=True);maximum=[r for r in result['rows'] if r['kind']=='Máximo del intervalo'];minimum=[r for r in result['rows'] if r['kind']=='Mínimo del intervalo']
        self.assertEqual([(r['x'],r['x_end'],r['plateau']) for r in maximum],[(1.,2.,2),(6.,6.,1)])
        self.assertEqual([r['x'] for r in minimum],[4.,7.]);self.assertEqual(result['maximum'],3);self.assertEqual(result['minimum'],-2)


class Interface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def settle(self,seconds=.1):
        end=time.monotonic()+seconds
        while time.monotonic()<end:self.app.processEvents();time.sleep(.003)
    def probe(self):
        from signallab_pc.plot_probe import PlotProbe
        widget=QWidget();layout=QVBoxLayout(widget);figure=Figure();canvas=FigureCanvasQTAgg(figure);layout.addWidget(canvas);toolbar=NavigationToolbar2QT(canvas,widget);axis=figure.add_subplot();axis.plot(np.arange(7),[0,2,0,1,0,-1,0]);probe=PlotProbe(canvas,toolbar,layout);canvas._signallab_window=widget;widget.show();canvas.draw();probe.open_inspector();self.settle();self.addCleanup(widget.close);self.addCleanup(probe.inspector.close);return probe
    def test_opening_measure_tab_populates_rows_and_enables_reading(self):
        probe=self.probe();dialog=probe.inspector;dialog.tabs.setCurrentIndex(1);self.settle()
        self.assertGreaterEqual(len(dialog.model.rows),2);self.assertTrue(dialog.read.isEnabled());self.assertTrue(dialog.search.isVisible());self.assertIn('Máximo: 2',dialog.measure_note.text())
    def test_scope_between_pins_uses_actual_coordinates_and_missing_pins_explain_why(self):
        probe=self.probe();dialog=probe.inspector;dialog.tabs.setCurrentIndex(1);dialog.scope.setCurrentIndex(2)
        self.assertIsNone(dialog.result);self.assertIn('Colocá A y B',dialog.measure_note.text())
        trace=probe.traces[0];probe.focus(trace,2,'a');probe.focus(trace,5,'b');dialog.search.click();self.assertEqual(dialog.result['first'],2);self.assertEqual(dialog.result['last'],5);self.assertEqual(dialog.result['maximum'],1)
    def test_marks_never_become_data_or_expand_axis_limits(self):
        probe=self.probe();dialog=probe.inspector;axis=probe.traces[0].axis;signature=probe.signature;box=axis.dataLim.bounds;dialog.tabs.setCurrentIndex(1);self.settle();probe.canvas.draw()
        self.assertEqual(probe.signature,signature);self.assertEqual(axis.dataLim.bounds,box);self.assertGreater(len(dialog.overlay.artists),0);self.assertGreater(len(dialog.model.rows),0)
    def test_command_discovery_excludes_owned_windows_and_local_commands(self):
        from signallab_pc.workbench import calculation_buttons
        page=QWidget();layout=QVBoxLayout(page);main=QPushButton('Calcular');main.setObjectName('primary');layout.addWidget(main)
        dialog=QDialog(page);local=QPushButton('Buscar',dialog);local.setObjectName('primary')
        inline=QWidget(page);inline.setProperty('keepLocalAction',True);other=QPushButton('Medir',inline);other.setObjectName('primary')
        self.assertEqual(calculation_buttons(page),[main]);dialog.close();page.close()
    def test_regression_real_workbench_cannot_hide_inspector_search(self):
        from signallab_pc.workbench import WorkbenchWindow
        from signallab_pc.workspaces import ROUTES
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.No),patch('signallab_pc.theme_presets.restore'):
            window=WorkbenchWindow();self.addCleanup(window.close);window.show();window.open_tool(ROUTES['system_analysis',0]);panel=window.pages[ROUTES['system_analysis',0]].panel
            panel.b.setText('1');panel.a.setText('1,1,1')
            # Use the panel's ordinary real result and the real parent/window tree.
            from signallab_pc.frequency_analysis import analyze_frequency
            data=analyze_frequency(Transfer([1],[1,1,1],domain='analog'),np.linspace(0,10,1025))
            panel.frequency_data=data;panel.draw_frequency();self.settle();probe=panel.canvas._signallab_probe;probe.open_inspector();dialog=probe.inspector;self.addCleanup(dialog.close);dialog.tabs.setCurrentIndex(1)
            for _ in range(3):window._refresh_primary_action();self.settle()
            self.assertTrue(dialog.search.isVisible());self.assertIs(window.current_calculate,panel.calculate_button);self.assertTrue(dialog.read.isEnabled());self.assertAlmostEqual(dialog.result['maximum'],2/np.sqrt(3),places=3)
            dialog.read.click();self.settle();self.assertTrue(probe.live)
            dialog.close();window.close()
    def test_narrow_inspector_keeps_search_and_point_buttons_inside_page(self):
        probe=self.probe();dialog=probe.inspector;dialog.tabs.setCurrentIndex(1);dialog.resize(620,600);self.settle()
        for button in (dialog.search,dialog.read,dialog.pin_a,dialog.pin_b,dialog.export):
            self.assertTrue(button.isVisible());self.assertGreaterEqual(button.geometry().left(),0);self.assertLessEqual(button.geometry().right(),button.parentWidget().width())


if __name__=='__main__':unittest.main()
