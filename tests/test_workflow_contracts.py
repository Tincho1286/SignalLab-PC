"""Real Qt widgets: transform/result/import -> system analysis -> reuse/export."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from numpy.testing import assert_allclose
from PySide6.QtWidgets import QApplication,QStatusBar
from signallab_pc.project import Project
from signallab_pc.workspaces import ROUTES
from signallab_pc.system_analysis_panel import SystemAnalysisPanel
from signallab_pc.transform_lab import TransformLab
from signallab_pc.symbolic import execute
from signallab_pc.filters import Transfer

SOURCE='sin(0.3*pi*(n-4))/(pi*(n-4))'


class Host:
    def __init__(self):self.project=Project();self.pages={};self._workers=[];self.current_operation=None;self.bar=QStatusBar()
    def statusBar(self):return self.bar
    def publish(self,value,**options):return self.project.add(value,**options)
    def _run_operation(self,label,compute,accept):accept(compute())
    def open_tool(self,route):
        self.current_operation=tuple(route)
        if self.current_operation not in self.pages:
            if self.current_operation in (ROUTES['transform_lab','z'],ROUTES['transform_lab','laplace']):panel=TransformLab(self,'z' if self.current_operation==ROUTES['transform_lab','z'] else 'laplace')
            else:panel=SystemAnalysisPanel(self)
            self.pages[self.current_operation]=SimpleNamespace(panel=panel)
    def send_system(self,*args):raise AssertionError('An expression must not be converted before choosing analysis capabilities.')
    def choose_record(self,*args,**kwargs):return None


class WorkflowContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.host=Host();self.widgets=[];self.warnings=[]
        self.warning_patch=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.warnings.append(str(a[2])));self.warning_patch.start()
        self.exception_patch=patch('sys.excepthook',side_effect=lambda kind,value,tb:self.warnings.append(kind.__name__+': '+str(value)));self.exception_patch.start()
    def tearDown(self):
        self.exception_patch.stop();self.warning_patch.stop()
        for widget in [*self.widgets,*[p.panel for p in self.host.pages.values()],self.host.bar]:widget.close();widget.deleteLater()
        self.app.processEvents()
    def transform(self):
        panel=TransformLab(self.host,'z');self.widgets.append(panel);panel.expression.setText(SOURCE);panel.lower.setText('0');panel.upper.setText('oo');panel.calculate_button.click()
        self.assertEqual(self.warnings,[]);return panel
    def calculated_analysis(self):
        panel=self.host.pages[self.host.current_operation].panel;panel.count.setText('101');panel.calculate_button.click();self.assertEqual(self.warnings,[])
        self.assertIsNotNone(panel.frequency_data);return panel
    def source_record(self):
        request=dict(operation='z_expression',expression=SOURCE,lower='0',upper='oo')
        return dict(request=request,result=execute(request))

    def test_impulse_alias_transform_to_analysis_and_cas(self):
        from signallab_pc.cas_transfer import payload
        from signallab_pc.cas_import import import_result
        from signallab_pc.cas_engine import empty_state,restore
        panel=TransformLab(self.host,'z');self.widgets.append(panel)
        for expression,delay,gain in [('Dirac(n)',0,1),('2*Dirac(n-3)',3,2),('Dirac(n+2)',-2,1)]:
            panel.expression.setText(expression);panel.lower.setText('-oo');panel.upper.setText('oo');panel.calculate_button.click()
            self.assertEqual(self.warnings,[]);self.assertTrue(panel.last['evaluated']);self.assertTrue(panel.analyze_system.isEnabled())
            imported=import_result(dict(state=empty_state(),cell='1',payload=payload(dict(request=dict(operation='z_expression',expression=expression,lower='-oo',upper='oo'),result=panel.last))))
            value=restore(imported['state']['results']['1'])
            from signallab_pc.symbolic import Z
            self.assertEqual((value-gain*Z**(-delay)).simplify(),0)
            panel.analyze_system.click();analysis=self.calculated_analysis()
            data=analysis.frequency_data
            assert_allclose(data.response,gain*np.exp(-1j*data.omega*delay),atol=2e-12)
            self.assertTrue(np.isfinite(data.response).all())

    def test_transform_button_to_general_system_analysis(self):
        source=self.transform();before=self.host.project.records();source.analyze_system.click();panel=self.calculated_analysis()
        self.assertIsNone(panel.system);self.assertIsNone(panel.analyzed_system)
        self.assertFalse(panel.result_tabs.isTabVisible(2));self.assertFalse(panel.result_tabs.isTabVisible(3))
        self.assertFalse(panel.expression_actions.isHidden());self.assertEqual(len(self.host.project.headers('system')),0)
        self.assertTrue(panel.roc_choice.isHidden());self.assertIsNone(self.host.project.get(panel._definition_id)['request']['roc_spec'])
        data=panel.frequency_data;self.assertTrue(np.isfinite(data.response[0]));self.assertTrue(np.isnan(data.response[30]));self.assertTrue(np.isfinite(data.delay[10]))
        saved=self.host.project.get(panel._definition_id);self.assertEqual(saved['result']['model_kind'],'expression');self.assertEqual(saved['request']['source_calculation']['request']['expression'],SOURCE)
        self.assertEqual(self.host.project.records()[:len(before)],before)

    def test_result_library_path_preserves_expression_and_conditions(self):
        from signallab_pc.result_expressions import send_expression
        record=self.source_record();key=self.host.publish(record);send_expression(self.host,key,'system');panel=self.calculated_analysis()
        saved=self.host.project.get(panel._definition_id)
        self.assertEqual(saved['request']['source_calculation'],record);self.assertIn('DTFT calculada',saved['result']['frequency_interpretation'])
        self.assertEqual(self.host.project.get(key),record)

    def test_system_import_path_accepts_nonrational_expression(self):
        record=self.source_record();key=self.host.publish(record);self.host.open_tool(ROUTES['system_analysis',0]);panel=self.host.pages[self.host.current_operation].panel
        panel.system_import.load_result(key);self.assertEqual(self.warnings,[]);self.assertEqual(panel.definition_mode.currentIndex(),1)
        self.calculated_analysis();self.assertIsNone(panel.system);self.assertTrue(panel.frequency_export.isEnabled())

    def test_general_hs_limits_derivative_and_export(self):
        from signallab_pc.result_expressions import ExpressionResult
        from signallab_pc.frequency_analysis import export_frequency
        self.host.open_tool(ROUTES['system_analysis',0]);panel=self.host.pages[self.host.current_operation].panel
        panel.load_expression(ExpressionResult('log(1+s)/s','s'));panel.w0.setText('0');panel.w1.setText('2');panel.count.setText('21');panel.calculate();self.assertEqual(self.warnings,[])
        data=panel.frequency_data;self.assertIsNotNone(data);assert_allclose(data.response[0],1,atol=1e-13);assert_allclose(data.delay[0],.5,atol=1e-13)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'response.json';export_frequency(data,path);document=json.loads(path.read_text())
            self.assertEqual(document['system']['format'],'signallab-expression-system');self.assertEqual(document['response_real'][0],1)

    def test_exported_definition_reloads_without_losing_original_support(self):
        from signallab_pc.result_expressions import send_expression
        key=self.host.publish(self.source_record());send_expression(self.host,key,'system');panel=self.calculated_analysis();original=panel.frequency_data.response.copy()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'system.json';self.host.project.export_record(panel._definition_id,path)
            panel.system_import.open_file(path);self.assertEqual(self.warnings,[]);panel=self.calculated_analysis()
        assert_allclose(panel.frequency_data.response,original,atol=1e-13,equal_nan=True)
        record=self.host.project.get(panel._definition_id);self.assertIn('DTFT calculada',record['result']['frequency_interpretation'])

    def test_bilateral_sinc_to_frequency_analysis_and_library_reload(self):
        from signallab_pc.result_expressions import expression_result,send_expression
        source=TransformLab(self.host,'z');self.widgets.append(source)
        source.expression.setText('sin(0.5*pi*(n-4))/(pi*(n-4))');source.lower.setText('-oo');source.upper.setText('oo');source.calculate_button.click()
        self.assertEqual(self.warnings,[]);self.assertFalse(source.last['evaluated']);self.assertTrue(source.last['convergence_empty'])
        self.assertTrue(source.analyze_system.isEnabled());self.assertIn('exp(iw)',source.analyze_system.text());source.analyze_system.click()
        panel=self.calculated_analysis();self.assertEqual(panel.definition_mode.currentIndex(),2)
        data=panel.frequency_data;assert_allclose(data.magnitude[:50],1,atol=1e-13);assert_allclose(data.magnitude[51:],0,atol=1e-13)
        assert_allclose(data.magnitude[50],.5,atol=1e-13);assert_allclose(data.delay[:50],4,atol=1e-13);self.assertTrue(np.isnan(data.delay[50:]).all())
        saved=self.host.project.get(panel._definition_id);self.assertEqual(saved['result']['model_kind'],'frequency');self.assertFalse(saved['request']['source_calculation']['result']['evaluated'])
        expression=expression_result(saved);self.assertEqual(expression.variable,'w');self.assertEqual(expression.units,'rad/muestra')
        send_expression(self.host,panel._definition_id,'system');panel=self.calculated_analysis();assert_allclose(panel.frequency_data.response,data.response,atol=1e-13)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ideal.json';self.host.project.export_record(panel._definition_id,path);panel.system_import.open_file(path);panel=self.calculated_analysis()
        assert_allclose(panel.frequency_data.response,data.response,atol=1e-13);self.assertIsNone(panel.system);self.assertTrue(panel.roc_choice.isHidden())

    def test_dtft_plot_button_opens_and_reopens_real_figure(self):
        from signallab_pc.symbolic_fourier_panel import SymbolicFourierPanel
        panel=SymbolicFourierPanel(self.host,discrete=True);self.widgets.append(panel)
        panel.expression.setText('sin(0.5*pi*(n-4))/(pi*(n-4))');panel.lower.setText('-oo');panel.upper.setText('oo');panel.calculate_button.click()
        from PySide6.QtCore import Qt
        self.assertIs(panel.tabs.cornerWidget(Qt.Corner.TopRightCorner),panel.sample_button)
        self.assertEqual(self.warnings,[]);self.assertTrue(panel.sample_button.isEnabled());panel.sample_button.click();self.app.processEvents()
        window=panel.output.canvas._signallab_window;self.widgets.append(window)
        self.assertTrue(window.isVisible());self.assertEqual(panel.output.views.currentIndex(),0);self.assertGreater(len(panel.output.figure.axes[0].lines),0)
        values=panel.output.result.values;self.assertAlmostEqual(abs(values[len(values)//2]),1);self.assertAlmostEqual(abs(values[0]),0)
        count = len(self.host.project.headers())
        window.hide();panel.tabs.setCurrentIndex(0);panel.sample_button.click();self.app.processEvents();self.assertTrue(window.isVisible());self.assertEqual(self.warnings,[])
        self.assertEqual(len(self.host.project.headers()), count)
        panel.expression.setText('0')
        self.assertFalse(panel.sample_button.isEnabled())
        self.assertFalse(window.isVisible())
        panel.calculate_button.click();self.app.processEvents()
        self.assertFalse(window.isVisible())
        panel.sample_button.click();self.app.processEvents()
        self.assertTrue(window.isVisible());assert_allclose(panel.output.result.values, 0)

    def test_dtft_result_reused_as_frequency_system(self):
        from signallab_pc.result_expressions import send_expression
        request=dict(operation='dtft_expression',expression='sin(0.3*pi*(n-4))/(pi*(n-4))',lower='-oo',upper='oo')
        key=self.host.publish(dict(request=request,result=execute(request)));send_expression(self.host,key,'system');panel=self.calculated_analysis()
        assert_allclose(panel.frequency_data.magnitude[:30],1,atol=1e-13);assert_allclose(panel.frequency_data.magnitude[31:],0,atol=1e-13)
        self.assertEqual(panel.definition_mode.currentIndex(),2);self.assertIsNone(panel.system)

    def test_unhandled_qt_button_failure_reaches_visible_error_handler(self):
        import sys
        from PySide6.QtWidgets import QPushButton
        from signallab_pc.runtime_diagnostics import install_exception_hook
        seen=[];button=QPushButton();self.widgets.append(button)
        def fail():raise NameError('Callback failure probe')
        button.clicked.connect(fail)
        with patch('signallab_pc.runtime_diagnostics.report_error',side_effect=lambda *a,**k:seen.append((a,k))):
            previous=install_exception_hook(self.app)
            try:button.click()
            finally:sys.excepthook=previous
        self.assertEqual(len(seen),1);self.assertIn('NameError',seen[0][1]['details']);self.assertEqual(self.warnings,[])

    def test_failed_presentation_sets_terminal_status_and_ignores_duplicate(self):
        from PySide6.QtWidgets import QMainWindow,QPushButton
        from signallab_pc.ui import SignalLabWindow
        shell=QMainWindow();self.widgets.append(shell);shell.cancel_button=QPushButton(shell);calls=[]
        def fail(result):calls.append(result);raise RuntimeError('Presentation probe')
        worker=SimpleNamespace(cancel_event=__import__('threading').Event(),on_success=fail,label='Calculation probe',origin=('Health','probe'))
        shell._workers=[worker];shell.statusBar().showMessage('Calculando…')
        with patch('signallab_pc.runtime_diagnostics.report_error') as report:
            SignalLabWindow._worker_finished(shell,worker,42);SignalLabWindow._worker_finished(shell,worker,42)
        self.assertEqual(calls,[42]);self.assertEqual(shell._workers,[]);self.assertIn('no se pudo presentar',shell.statusBar().currentMessage());report.assert_called_once()

    def test_worker_diagnostic_preserves_trace_and_stays_local(self):
        from signallab_pc.ui import _OperationWorker
        from signallab_pc.runtime_diagnostics import diagnostic
        def fail():raise ArithmeticError('Health worker probe')
        worker=_OperationWorker(fail);seen=[];worker.signals.failed.connect(lambda sender,error:seen.append(error));worker.run()
        self.assertEqual(seen,['Health worker probe']);self.assertIn('ArithmeticError',worker.failure_details)
        with tempfile.TemporaryDirectory() as folder:
            text,path=diagnostic(seen[0],worker.failure_details,'Health probe',folder)
            self.assertEqual(path.parent,Path(folder));self.assertIn('ArithmeticError',path.read_text(encoding='utf-8'));self.assertIn('Referencia:',text)

    def test_numerical_frequency_limits_reach_report_and_export(self):
        from signallab_pc.frequency_analysis import export_frequency
        self.host.open_tool(ROUTES['system_analysis',0]);panel=self.host.pages[self.host.current_operation].panel
        panel.domain.setCurrentIndex(1);panel.definition_mode.setCurrentIndex(1);panel.transfer_formula.setText('1/(1-z^(-1))')
        panel.w0.setText('0');panel.w1.setText('2*pi');panel.count.setText('9');panel.calculate_button.click();self.assertEqual(self.warnings,[])
        data=panel.frequency_data;self.assertTrue(np.isnan(data.response[[0,-1]]).all());self.assertTrue(np.isfinite(data.response[1:-1]).all())
        self.assertTrue(np.isnan(data.delay[[0,-1]]).all())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'response.json';export_frequency(data,path);saved=json.loads(path.read_text())
            self.assertEqual(len(saved['frequency']),9);self.assertIsNone(saved['response_real'][0]);self.assertIsNone(saved['response_real'][-1]);self.assertIsNone(saved['group_delay'][0])
        panel.domain.setCurrentIndex(0);panel.transfer_formula.setText('(s^2+2*s+1)/(s^2+3*s+2)')
        panel.w0.setText('1e160');panel.w1.setText('1e200');panel.count.setText('3');panel.calculate_button.click();self.assertEqual(self.warnings,[])
        self.assertTrue(np.isfinite(panel.frequency_data.response).all());assert_allclose(panel.frequency_data.magnitude,1,atol=1e-13)

    def test_cas_library_inverse_preserves_roc_and_requires_unknown_selection(self):
        from signallab_pc.cas_panel import CasWorksheet
        from signallab_pc.cas_transfer import payload
        from signallab_pc.result_expressions import send_expression
        from signallab_pc.signal_notation import read
        from signallab_pc.symbolic import N,T
        for domain,roc in [('digital',{'mode':'left'}),('digital',{'mode':'radius','radius':.75}),('analog',{'mode':'left'}),('analog',{'mode':'line','sigma':-1})]:
            system=Transfer([1],[1,-.5] if domain=='digital' else [1,.5],domain=domain,roc=roc);key=self.host.publish(system)
            sheet=CasWorksheet(self.host);self.widgets.append(sheet);sheet.import_result(payload(system),'Sistema',key)
            sheet.input.setPlainText('simplify(r1)');sheet.input.evaluateRequested.emit();self.assertEqual(sheet.entries[-1]['status'],'done')
            result_id=sheet.entries[-1]['result_id'];send_expression(self.host,result_id,'inverse');panel=self.host.pages[self.host.current_operation].panel
            if domain=='digital':
                self.assertEqual(panel.roc.currentIndex(),1 if roc['mode']=='left' else 2);panel.include_samples.setChecked(False)
                if roc['mode']=='radius':self.assertEqual(float(panel.radius.text()),.75)
            else:
                self.assertEqual(panel.interpretation.currentIndex(),1);self.assertEqual(panel.laplace_roc.currentIndex(),1 if roc['mode']=='left' else 2)
                if roc['mode']=='line':self.assertEqual(float(panel.sigma.text()),-1)
            panel.analyze_system.click();self.assertEqual(self.warnings,[])
            analysis=self.host.pages[self.host.current_operation].panel;self.assertEqual(analysis.roc_choice.currentIndex(),1 if roc['mode']=='left' else 2)
            self.host.open_tool(ROUTES['transform_lab','z' if domain=='digital' else 'laplace'])
            panel.calculate_button.click();self.assertEqual(self.warnings,[]);self.assertTrue(panel.last['evaluated'])
            value=read(panel.last['result'],('n',))
            if domain=='digital':self.assertAlmostEqual(float(value.subs(N,-1)),-2 if roc['mode']=='left' else 0)
            else:self.assertAlmostEqual(float(value.subs(next(v for v in value.free_symbols if v.name=='t'),-1)),-float(np.exp(.5)))
            sheet.input.setPlainText('2*r2');sheet.input.evaluateRequested.emit();changed=sheet.entries[-1]['result_id']
            send_expression(self.host,changed,'inverse');panel=self.host.pages[self.host.current_operation].panel
            self.assertEqual((panel.roc if domain=='digital' else panel.laplace_roc).currentIndex(),-1)
            before=len(self.host.project.records());panel.calculate_button.click();self.assertEqual(len(self.host.project.records()),before)
            self.assertEqual(len(self.warnings),1);self.warnings.clear()

    def test_cas_system_roc_and_clock_reach_analysis_and_survive_reload(self):
        from signallab_pc.cas_panel import CasWorksheet
        from signallab_pc.cas_transfer import payload
        for domain,roc,period in [('digital',{'mode':'left'},.01),('analog',{'mode':'left'},None)]:
            system=Transfer([1],[1,-.5] if domain=='digital' else [1,.5],domain=domain,roc=roc,sample_period_s=period);key=self.host.publish(system)
            sheet=CasWorksheet(self.host);self.widgets.append(sheet);sheet.import_result(payload(system),'Sistema',key)
            sheet.input.setPlainText('simplify(r1)');sheet.input.evaluateRequested.emit();self.assertEqual(sheet.entries[-1]['status'],'done')
            saved=self.host.project.get(sheet.entries[-1]['result_id']);self.assertEqual(saved['cas_answer']['system_context']['roc'],roc)
            sheet.send_result('digital' if domain=='digital' else 'analog');panel=self.host.pages[self.host.current_operation].panel
            self.assertEqual(panel.roc_choice.currentIndex(),1);panel.count.setText('17');panel.calculate_button.click();self.assertEqual(self.warnings,[])
            self.assertEqual(panel.system.roc,roc);self.assertEqual(panel.system.sample_period_s,period)
            self.assertIsNone(panel.frequency_data)
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'system.json';self.host.project.export_record(panel._definition_id,path);panel.system_import.open_file(path)
                panel.calculate_button.click();self.assertEqual(self.warnings,[]);self.assertEqual(panel.system.roc,roc)
                self.assertEqual(panel.system.sample_period_s,period)

    def test_cas_worksheet_rewrite_and_send_to_frequency_analysis(self):
        from signallab_pc.cas_panel import CasWorksheet
        from signallab_pc.cas_transfer import payload
        sheet=CasWorksheet(self.host);self.widgets.append(sheet)
        request=dict(operation='dtft_expression',expression='sin(pi*n/2)/(pi*n)',lower='-oo',upper='oo');record=dict(request=request,result=execute(request));key=self.host.publish(record)
        sheet.import_result(payload(record),'DTFT',key);sheet.input.setPlainText('simplify(r1)');sheet.input.evaluateRequested.emit()
        self.assertEqual(sheet.entries[-1]['status'],'done');saved=self.host.project.get(sheet.entries[-1]['result_id']);self.assertEqual(saved['cas_answer']['frequency_units'],'rad/muestra')
        sheet.send_result('frequency');panel=self.calculated_analysis();self.assertEqual(panel.definition_mode.currentIndex(),2)
        self.assertEqual(panel.frequency_data.units,'rad/muestra');self.assertEqual(self.warnings,[])

    def test_conditional_dtft_plot_and_export_keep_undefined_frequency(self):
        from signallab_pc.symbolic_fourier_panel import SymbolicFourierPanel
        panel=SymbolicFourierPanel(self.host,discrete=True);self.widgets.append(panel)
        panel.expression.setText('1/n');panel.lower.setText('1');panel.upper.setText('oo');panel.calculate_button.click();self.assertEqual(self.warnings,[])
        self.assertTrue(panel.sample_button.isEnabled());panel.start.setText('-1');panel.stop.setText('1');panel.count.setText('5');panel.sample_button.click();self.app.processEvents()
        self.assertEqual(self.warnings,[]);self.assertEqual(panel.masked.data['samples'][2],None);self.assertEqual(panel.masked.table.model.value(2,1),'No definido')
        window=panel.masked.canvas._signallab_window;self.widgets.append(window);self.assertTrue(window.isVisible())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'grid.json';panel.masked.save(path);data=json.loads(path.read_text());self.assertEqual(data['samples'][2],None);self.assertEqual(len(data['samples']),5)
        panel.expression.setText('(1/2)^n');panel.lower.setText('0');panel.calculate_button.click();self.assertFalse(panel.tabs.isTabVisible(panel.masked_index))

    def test_rational_transfer_still_retains_numeric_system(self):
        from signallab_pc.result_expressions import ExpressionResult
        self.host.open_tool(ROUTES['system_analysis',0]);panel=self.host.pages[self.host.current_operation].panel
        panel.load_expression(ExpressionResult('z^2/(z-1/2)','z'));panel.count.setText('21');panel.calculate();self.assertEqual(self.warnings,[])
        self.assertIsInstance(panel.system,Transfer);self.assertEqual(panel.system.advance,1)
        z=np.exp(1j*panel.frequency_data.omega);assert_allclose(panel.frequency_data.response,z*z/(z-.5),atol=2e-13)
        self.assertTrue(panel.expression_actions.isHidden());self.assertTrue(panel.result_tabs.isTabVisible(2));self.assertFalse(panel.roc_choice.isHidden())



    def test_report_header_opens_and_selects_available_figures(self):
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QWidget,QVBoxLayout,QTabWidget
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg,NavigationToolbar2QT
        from signallab_pc.plot_view import install_enlarge
        tabs=QTabWidget();self.widgets.append(tabs);canvases=[]
        for label in ('Frecuencia','Polos y ceros'):
            page=QWidget();box=QVBoxLayout(page);tabs.addTab(page,label)
            canvas=FigureCanvasQTAgg(Figure());bar=NavigationToolbar2QT(canvas,page);box.addWidget(bar);box.addWidget(canvas)
            install_enlarge(bar);canvases.append(canvas);self.widgets.append(canvas._signallab_window)
        report=QWidget();tabs.addTab(report,'Informe');tabs.resize(820,480);tabs.show();self.app.processEvents()
        launcher=tabs.cornerWidget(Qt.Corner.TopRightCorner);self.assertIsNotNone(launcher);self.assertFalse(launcher.isEnabled())
        for canvas in canvases:canvas.figure.add_subplot(111).plot([0,1],[0,1]);canvas.draw()
        self.app.processEvents()
        for canvas in canvases:canvas._signallab_window.hide()
        tabs.setCurrentWidget(report);self.app.processEvents();self.assertTrue(launcher.isVisible());launcher.click();self.app.processEvents()
        self.assertTrue(canvases[0]._signallab_window.isVisible());canvases[0]._signallab_window.hide()
        launcher.rebuild();self.assertEqual([a.text() for a in launcher.menu.actions()],['Frecuencia','Polos y ceros'])
        launcher.menu.actions()[1].trigger();self.app.processEvents();self.assertTrue(canvases[1]._signallab_window.isVisible())
        tabs.setTabVisible(1,False);launcher.rebuild();self.assertEqual(len(launcher.menu.actions()),1)
        tabs.setTabEnabled(0,False);launcher.refresh();self.assertFalse(launcher.isEnabled());self.assertEqual(launcher.available(),[])
        self.assertEqual(self.warnings,[])

    def test_measures_plot_action_stays_with_report(self):
        from PySide6.QtCore import Qt
        from signallab_pc.expression_measures_panel import ExpressionMeasuresPanel
        panel=ExpressionMeasuresPanel(self.host,'interval');self.widgets.append(panel);panel.resize(1040,620);panel.show()
        from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
        from signallab_pc.plot_view import install_enlarge
        for toolbar in panel.findChildren(NavigationToolbar2QT):install_enlarge(toolbar)
        self.assertIs(panel.tabs.cornerWidget(Qt.Corner.TopRightCorner),panel.sample_button);self.assertFalse(panel.sample_button.isEnabled())
        panel.domain.setCurrentIndex(1);panel.expression.setText('Impulse(n)');panel.lower.setText('-2');panel.upper.setText('2');panel.start.setText('-2');panel.stop.setText('2');panel.calculate_button.click()
        self.assertEqual(self.warnings,[]);self.assertTrue(panel.sample_button.isEnabled());self.app.processEvents();self.assertTrue(panel.sample_button.isVisible())
        panel.sample_button.click();self.app.processEvents();self.assertEqual(self.warnings,[]);window=panel.output.canvas._signallab_window;self.widgets.append(window);self.assertTrue(window.isVisible())
        assert_allclose(panel.output.result.values,[0,0,1,0,0]);self.assertAlmostEqual(panel.output.result.metadata['energy'],1)
        count = len(self.host.project.headers())
        window.hide();panel.tabs.setCurrentIndex(0);panel.sample_button.click();self.app.processEvents();self.assertTrue(window.isVisible());self.assertEqual(self.warnings,[])
        self.assertEqual(len(self.host.project.headers()), count)

    def test_temporal_panel_rejects_incompatible_roc_without_publishing(self):
        from signallab_pc.temporal_panel import TemporalPanel
        panel = TemporalPanel(self.host);self.widgets.append(panel)
        for domain, denominator in (('digital', [1,-2]), ('analog', [1,-1])):
            with self.subTest(domain=domain):
                system = Transfer([1], denominator, domain, roc={'mode':'left'})
                key = self.host.project.add(system)
                panel.set_system(system, key);panel.stimulus.setCurrentIndex(1);panel.count.setText('5')
                count = len(self.host.project.headers())
                panel.calculate_button.click()
                self.assertIn('cola anticausal', self.warnings[-1])
                self.assertIn('inversa', self.warnings[-1])
                self.assertEqual(len(self.host.project.headers()), count)
                self.assertIsNone(panel.output.result)
                panel.set_system(Transfer([1], denominator, domain, roc={'mode':'right'}))
                self.warnings.clear()
                panel.calculate_button.click()
                self.assertEqual(self.warnings, [])
                self.assertIsNotNone(panel.output.result)
                panel.output.result = None

    def test_z_reciprocal_tail_from_direct_to_inverse(self):
        panel = TransformLab(self.host, 'z');self.widgets.append(panel)
        panel.expression.setText('Step(n-1)/n');panel.lower.setText('1');panel.upper.setText('oo')
        panel.calculate_button.click();panel.to_inverse()
        self.assertEqual(panel.roc.currentIndex(), 0)
        panel.include_samples.setChecked(True);panel.start.setText('-1');panel.count.setText('5')
        panel.calculate_button.click()
        self.assertEqual(self.warnings, [])
        _, result, _, _, signal = panel.records[panel.record_key()]
        self.assertEqual(result['method'], 'reciprocal_series_pairs')
        assert_allclose(signal.values, [0,0,1,.5,1/3])


if __name__=='__main__':unittest.main()
