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
from signallab_pc.model import Signal

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
            elif route[1] in ('dtft_symbolic','fourier_symbolic'):
                from signallab_pc.symbolic_fourier_panel import SymbolicFourierPanel
                panel=SymbolicFourierPanel(self,inverse=bool(route[2]),discrete=route[1]=='dtft_symbolic')
            else:panel=SystemAnalysisPanel(self)
            self.pages[self.current_operation]=SimpleNamespace(panel=panel)
    def open_cas(self):
        from signallab_pc.cas_panel import CasWorksheet
        from signallab_pc.cas_reference import CAS_ROUTE
        if CAS_ROUTE not in self.pages:self.pages[CAS_ROUTE]=CasWorksheet(self)
        self.current_operation=CAS_ROUTE

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
        for widget in [*self.widgets,*[getattr(p,"panel",p) for p in self.host.pages.values()],self.host.bar]:widget.close();widget.deleteLater()
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
        request=dict(operation='dtft_expression',expression='sin(0.3*pi*(n-4))/(pi*(n-4))',lower='-oo',upper='oo')
        from signallab_pc.symbolic_fourier_panel import SymbolicFourierPanel
        source=SymbolicFourierPanel(self.host,discrete=True);self.widgets.append(source)
        source.expression.setText(request['expression']);source.lower.setText('-oo');source.upper.setText('oo')
        source.calculate_button.click()
        source.to_cas_button.menu().aboutToShow.emit()
        source.to_cas_button.menu().actions()[0].trigger()
        sheet=self.host.pages[self.host.current_operation]
        self.assertEqual(sheet.entries[-1]['status'],'done',sheet.entries[-1].get('error'))
        sheet.input.setPlainText('subst(r1,w,3*pi/10)');sheet.calculate()
        from signallab_pc.cas_engine import restore
        import sympy as sp
        expected=sp.exp(-sp.I*4*3*sp.pi/10)/2
        self.assertEqual(sp.simplify(restore(sheet.state['results']['2'])-expected),0)
        source.reuse_button.menu().aboutToShow.emit()
        action=next(action for action in source.reuse_button.menu().actions() if action.text()=='Analizar como sistema H(w)')
        action.trigger()
        panel=self.calculated_analysis()
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

    def test_dtft_numeric_input_copy_preserves_period_origin_and_domain(self):
        import sympy as sp
        from signallab_pc.cas_engine import restore
        from signallab_pc.symbolic import N
        from signallab_pc.inverse_dtft_panel import InverseDtftPanel
        from signallab_pc.symbolic_fourier_panel import SymbolicFourierPanel
        from signallab_pc.fourier_workflow import prepare_fourier_inputs
        numeric=InverseDtftPanel(self.host)
        algebra=SymbolicFourierPanel(self.host,inverse=True,discrete=True)
        self.widgets.extend((numeric,algebra))
        numeric.source.origin.setText('0')
        numeric.source.expression.setText('where(w<=pi/3,1,0)')
        numeric.source._expression_origin=(numeric.source.expression.text(),None)
        numeric.source._expression_frequency_condition='w>=0'
        one=SimpleNamespace(panel=numeric,tool_item=ROUTES['inverse_dtft',0])
        two=SimpleNamespace(panel=algebra,tool_item=ROUTES['dtft_symbolic',1])
        prepare_fourier_inputs(one,two).apply()
        self.assertEqual(algebra._frequency_origin,'0')
        self.assertEqual(algebra._frequency_condition,'w>=0')
        algebra.calculate_button.click()
        self.assertEqual(self.warnings,[])
        self.assertEqual(restore(algebra.last[1]['cas_encoded']).subs(N,0),sp.Rational(1,6))

    def test_dtft_send_button_preserves_frequency_exclusions(self):
        from signallab_pc.symbolic_fourier_panel import SymbolicFourierPanel
        panel=SymbolicFourierPanel(self.host,discrete=True);self.widgets.append(panel)
        panel.expression.setText('1/n');panel.lower.setText('1')
        panel.calculate_button.click()
        panel.to_cas_button.menu().aboutToShow.emit()
        panel.to_cas_button.menu().actions()[0].trigger()
        sheet=self.host.pages[self.host.current_operation]
        self.assertEqual(self.warnings,[])
        self.assertEqual(sheet.entries[-1]['status'],'done',sheet.entries[-1].get('error'))
        self.assertEqual(sheet.entries[-1]['answer']['frequency_units'],'rad/muestra')
        response=self.host.publish({'result':{'result':'exp(I*w)','output_variable':'w','frequency_units':'rad/muestra'}})
        from signallab_pc.cas_transfer import payload
        from signallab_pc.cas_import import import_result
        typed=import_result({'cell':1,'payload':payload(self.host.project.get(response))})
        transformed=execute(dict(operation='cas_worksheet',state=typed['state'],cell=2,source='conj(r1)'))
        self.assertEqual(transformed['expression'],'exp(-I*w)')
        sheet.input.setPlainText('subst(r1,w,0)');sheet.input.evaluateRequested.emit()
        self.assertEqual(sheet.entries[-1]['status'],'error')
        self.assertIn('fuera del dominio',sheet.entries[-1]['error'])
        sheet.input.setPlainText('subst(r1,w,pi)');sheet.input.evaluateRequested.emit()
        self.assertEqual(sheet.entries[-1]['status'],'done',sheet.entries[-1].get('error'))
        self.assertEqual(sheet.entries[-1]['answer']['expression'],'-log(2)')

    def test_discrete_bins_do_not_become_temporal_filter_inputs(self):
        from signallab_pc.operations import dft
        from signallab_pc.windowing import multiply_signals,window_impulse
        from signallab_pc.state_simulation_inputs import prepare_inputs
        from signallab_pc.state_space import StateModel
        bins=dft(Signal([1,2,3]))
        model=StateModel([[.5]],[[1]],[[1]],[[0]],dt=1)
        for operation in (lambda:multiply_signals(bins,bins),lambda:window_impulse(bins),
                          lambda:prepare_inputs(model,[bins])):
            with self.assertRaisesRegex(ValueError,'señal temporal'):operation()

    def test_spectral_roles_remain_distinct_in_comparison_and_energy(self):
        from signallab_pc.fourier import energy_density
        from signallab_pc.result_comparison import compare
        filt=Signal([1,1,1],-1,1,'rad/muestra',domain='frequency',metadata={'operation':'frequency_filter'})
        with self.assertRaisesRegex(ValueError,'respuesta de un filtro'):energy_density(filt)
        density=filt.copy_with(metadata={'operation':'energy_density'})
        with self.assertRaisesRegex(ValueError,'misma clase'):compare(filt,density)

    def test_piecewise_cas_and_report_use_readable_mathematical_conditions(self):
        from signallab_pc.frequency_filter_panel import FrequencyFilterPanel
        from signallab_pc.cas_presentation import presentation_html
        from signallab_pc.cas_engine import calculate
        from signallab_pc.math_display import latex
        from signallab_pc.vector_math import render_latex
        from signallab_pc.expression_structure import parse_cases,periodic_display
        from signallab_pc.report_view import ReportView
        panel=FrequencyFilterPanel(self.host);self.widgets.append(panel)
        panel.h.expression.setText('Piecewise((1,abs(w)<=pi/5),(0,(abs(w)>pi/5) & (abs(w)<=pi/2)),(2,(abs(w)>pi/2) & (abs(w)<=pi)))')
        panel.calculate_button.click();panel.cas_definition.trigger()
        sheet=self.host.pages[self.host.current_operation]
        answer=sheet.entries[-1]['answer']
        body=presentation_html(sheet.report,answer['presentation'],900)
        self.assertNotIn('<pre',body)
        self.assertIn('Frecuencia dentro del período',body)
        self.assertNotIn('Fuera de estos casos',body)
        partial='Piecewise((1,Abs(-pi+Mod(w+pi,2*pi))<pi/5))'
        partial_view=ReportView();self.widgets.append(partial_view)
        self.assertIn('Fuera de estos casos',partial_view._render_formula(partial))
        shown,definitions=periodic_display(answer['presentation']['text'])
        self.assertEqual(len(definitions),1)
        cases=parse_cases(shown)
        self.assertEqual([value for value,_ in cases[0]],['1','0','2'])
        for expression,expected in [('subst(r1,w,0)','1'),('subst(r1,w,pi/3)','0'),('subst(r1,w,3*pi/4)','2')]:
            result=calculate(dict(cell=2,state=sheet.state,source=expression))
            self.assertEqual(result['expression'],expected)
        self.assertEqual(latex('Eq(0,n)'),'n=0')
        self.assertEqual(latex('Eq(n,0)'),'n=0')
        self.assertEqual(latex('Ne(n,0)'),r'n\neq 0')
        for expression in ('Eq(n,0)','Abs(w)','Mod(w+pi,2*pi)','(w>0) & (w<=pi)','And(w>0,w<pi)'):
            render_latex(latex(expression))
        view=ReportView();self.widgets.append(view)
        formula=view._render_formula('h[n] = '+self.host.project.get(panel.impulse_key)['result']['result'])
        self.assertIsNotNone(formula)
        nested='Piecewise((1,w<0),(Piecewise((2,w<1),(3,True)),True))'
        self.assertEqual(parse_cases(nested),([('1','w < 0'),('2','w < 1')],'3'))
        self.assertEqual(self.warnings,[])

    def test_ideal_filter_sends_each_formula_and_selected_samples(self):
        from signallab_pc.frequency_filter_panel import FrequencyFilterPanel
        from signallab_pc.cas_engine import restore
        panel=FrequencyFilterPanel(self.host);self.widgets.append(panel)
        panel.h.expression.setText('Piecewise((exp(-2*i*w), (w >= -pi/2) & (w <= pi/2)), (0, True))')
        panel.calculate_button.click()
        self.assertTrue(panel.cas_definition.isEnabled())
        self.assertTrue(panel.cas_impulse.isEnabled())
        self.assertEqual(panel.reuse_button.text(),'Usar filtro en…')
        self.assertIs(panel.cas_button.parentWidget(),panel.reuse_button.parentWidget())
        self.assertIs(panel.view.actions.parentWidget(),panel.tabs.parentWidget())
        panel.reuse_button.menu().aboutToShow.emit()
        inverse=next(action for action in panel.reuse_button.menu().actions() if action.text()=='DTFT inversa algebraica')
        inverse.trigger()
        destination=self.host.pages[self.host.current_operation].panel
        self.assertIn('Piecewise',destination.expression.text())
        panel.cas_definition.trigger();sheet=self.host.pages[self.host.current_operation]
        self.assertEqual(sheet.input.toPlainText(),'r1')
        response=execute(dict(operation='cas_worksheet',state=sheet.state,cell=3,source='subst(r1,w,pi)'))
        self.assertEqual(response['expression'],'0')
        panel.cas_impulse.trigger()
        self.assertEqual(sheet.input.toPlainText(),'r2')
        self.assertEqual(sheet.entries[-1]['status'],'done',sheet.entries[-1].get('error'))
        check=execute(dict(operation='cas_worksheet',state=sheet.state,cell=3,source='subst(r2,n,2)'))
        self.assertEqual(check['expression'],'1/2')
        with self.assertRaisesRegex(ValueError,'fuera del dominio'):
            execute(dict(operation='cas_worksheet',state=sheet.state,cell=3,source='subst(r2,n,1/2)'))
        sheet.input.setPlainText('simplify(r2)')
        panel.selector.setCurrentIndex(1)
        self.assertEqual(panel.reuse_button.text(),'Usar señal en…')
        panel.cas_samples.trigger()
        self.assertEqual(sheet.input.toPlainText(),'simplify(r2)')
        self.assertEqual(restore(sheet.state['results']['3']).shape,(65,2))
        self.assertEqual(self.warnings,[])

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


    def test_fir_window_switch_ignores_hidden_manual_length(self):
        from signallab_pc.course_tools_panel import CourseToolsPanel
        panel=CourseToolsPanel(self.host,'fir');self.widgets.append(panel)
        panel.show();self.app.processEvents()
        self.assertTrue(panel.form.isRowVisible(panel.fields['taps']))
        self.assertNotIn('search',panel.fields)
        panel.band_edges.edits[1].setText('0.32*pi')
        panel.fields['dp'].setText('0.03');panel.fields['ds'].setText('0.03')
        panel.calculate_button.click()
        self.assertEqual(self.warnings,[])
        self.assertIn('dentro de tolerancias',panel.report.toPlainText())
        self.assertGreater(len(next(item for item in panel.items if isinstance(item,Transfer)).b),158)
        panel.fields['taps'].setText('158')
        panel.calculate_button.click()
        self.assertEqual(self.warnings,[])
        self.assertIn('Longitud fijada manualmente',panel.report.toPlainText())
        self.assertEqual(len(next(item for item in panel.items if isinstance(item,Transfer)).b),158)
        panel.fields['taps'].setText('entrada manual inválida')
        panel.fields['window'].setCurrentIndex(panel.fields['window'].findData('hamming'))
        self.assertFalse(panel.form.isRowVisible(panel.fields['taps']))
        panel.calculate_button.click()
        self.assertEqual(self.warnings,[])
        self.assertEqual(sum(isinstance(item,Transfer) for item in panel.items),1)
        self.assertIn('Búsqueda automática',panel.report.toPlainText())


    def test_vertical_range_keeps_db_samples_and_frequency_zoom(self):
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
        from matplotlib.figure import Figure
        from signallab_pc.plot_limits_dialog import VerticalRangeDialog
        from signallab_pc.plot_scale import apply_stable_scale
        figure=Figure();canvas=FigureCanvasQTAgg(figure);self.widgets.append(canvas)
        axis=figure.add_subplot(211);axis.set_ylabel('Módulo (dB)')
        frequencies=np.linspace(0,np.pi,401)
        values=np.where(frequencies<.3*np.pi,0.,-48.-8*np.sin(20*frequencies)**2)
        values[-1]=-400.
        line=axis.plot(frequencies,values)[0];axis.set_xlim(.1,3.1)
        phase=figure.add_subplot(212);phase.set_ylabel('Fase (rad)');phase.plot(frequencies,-frequencies)
        original_phase=phase.get_ylim();original_x=axis.get_xlim()
        self.assertEqual(apply_stable_scale(figure),[axis]);self.assertGreater(axis.get_ylim()[0],-100)
        dialog=VerticalRangeDialog(canvas);self.widgets.append(dialog)
        dialog.mode.setCurrentIndex(dialog.mode.findData('full'));dialog.apply()
        apply_stable_scale(figure);self.assertLessEqual(axis.get_ylim()[0],-400)
        dialog=VerticalRangeDialog(canvas);self.widgets.append(dialog)
        dialog.mode.setCurrentIndex(dialog.mode.findData('manual'))
        dialog.minimum.setText('-70');dialog.maximum.setText('2');dialog.apply()
        apply_stable_scale(figure);self.assertEqual(axis.get_ylim(),(-70.,2.))
        self.assertEqual(axis.get_xlim(),original_x);self.assertEqual(phase.get_ylim(),original_phase)
        assert_allclose(line.get_ydata(),values)



    def test_inverse_z_automatic_scope_does_not_block_an_infinite_sequence(self):
        panel=TransformLab(self.host,'z');self.widgets.append(panel)
        panel.mode.setCurrentIndex(1);panel.sample_scope.setCurrentIndex(1)
        panel.expression.setText('-18/(z+1)');panel.start.setText('-2');panel.count.setText('7')
        panel.calculate_button.click()
        self.assertEqual(self.warnings,[]);self.assertTrue(panel.last['evaluated'])
        self.assertEqual(panel.last['origin'],-2)
        self.assertEqual([v[0] for v in panel.last['numeric_samples']],[0,0,0,-18,18,-18,18])
        self.assertIn('El soporte no es finito',panel.report.toPlainText())
        self.assertFalse(panel.start.isHidden());self.assertFalse(panel.count.isHidden())
        self.assertTrue(panel.to_cas_button.isEnabled());self.assertTrue(panel.reuse_button.isEnabled())
        panel.expression.setText('z^2+3/z');panel.calculate_button.click()
        self.assertEqual(self.warnings,[]);self.assertEqual(panel.last['origin'],-2)
        self.assertEqual([v[0] for v in panel.last['numeric_samples']],[1,0,0,3])
        panel.expression.setText('1/(1-1000000/z)');panel.start.setText('0');panel.count.setText('65')
        panel.calculate_button.click()
        self.assertEqual(self.warnings,[]);self.assertTrue(panel.last['evaluated'])
        self.assertIsNone(panel.last['numeric_samples']);self.assertIn('No se generó el gráfico',panel.report.toPlainText())
        self.assertTrue(panel.to_cas_button.isEnabled());self.assertTrue(panel.reuse_button.isEnabled())


    def test_system_definition_survives_invalid_frequency_view(self):
        panel=SystemAnalysisPanel(self.host);self.widgets.append(panel)
        panel.definition_mode.setCurrentIndex(1);panel.domain.setCurrentIndex(1)
        panel.transfer_formula.setText('1/(1-1/(2*z))');panel.w0.setText('pi');panel.w1.setText('0')
        panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertIsNotNone(panel._definition_id)
        self.assertIsNotNone(panel.system);self.assertIsNone(panel.frequency_data)
        self.assertIn('Intervalo de frecuencia',panel.report.toPlainText())
        panel.w0.setText('0');panel.w1.setText('pi');panel.count.setText('1000000000000000');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertIsNotNone(panel.system);self.assertIsNone(panel.frequency_data)
        self.assertIn('Rejilla de frecuencia',panel.report.toPlainText())

    def test_system_exact_only_definition_remains_reusable(self):
        from signallab_pc.result_expressions import expression_result
        panel=SystemAnalysisPanel(self.host);self.widgets.append(panel)
        panel.definition_mode.setCurrentIndex(1);panel.domain.setCurrentIndex(1)
        panel.transfer_formula.setText('10^400/(1-1/(2*z))');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertIsNotNone(panel._definition_id)
        self.assertIsNone(panel.system);self.assertIsNone(panel.frequency_data)
        self.assertFalse(panel.expression_actions.isHidden())
        record=self.host.project.get(panel._definition_id)
        self.assertEqual(expression_result(record).variable,'z')
        self.assertIn('realización numérica',panel.report.toPlainText())

    def test_z_invalid_view_fields_preserve_formula_and_finite_automatic_scope(self):
        panel=TransformLab(self.host,'z');self.widgets.append(panel);panel.mode.setCurrentIndex(1)
        panel.expression.setText('-18/(z+1)');panel.start.setText('mal');panel.count.setText('0');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertTrue(panel.last['evaluated'])
        self.assertIsNone(panel.last['numeric_samples']);self.assertTrue(panel.to_cas_button.isEnabled())
        self.assertIn('No se generó el gráfico',panel.report.toPlainText())
        panel.sample_scope.setCurrentIndex(1);panel.expression.setText('1-18/z');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertEqual([v[0] for v in panel.last['numeric_samples']],[1,-18])

    def test_fir_window_design_survives_frequency_memory_limit(self):
        from signallab_pc.fir_window_panel import FirWindowPanel
        panel=FirWindowPanel(self.host);self.widgets.append(panel)
        panel.h.expression.setText('1');panel.length.setText('9')
        panel.frequency.count.setText('1000000000000000');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertIsNotNone(panel.system)
        self.assertIsNone(panel.frequency.data);self.assertTrue(len(panel.series_keys)>0)
        self.assertIn('Rejilla de frecuencia',panel.report.toPlainText())

    def test_ideal_filter_retains_formula_cas_and_reuse_when_temporal_view_fails(self):
        from signallab_pc.frequency_filter_panel import FrequencyFilterPanel
        panel=FrequencyFilterPanel(self.host);self.widgets.append(panel)
        panel.h.expression.setText('where(abs(w)<=pi/2,1,0)');panel.h.count.setText('33');panel.h.step.setText('pi/16')
        panel.count.setText('1');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertIsNotNone(panel.algebraic_key);self.assertIsNotNone(panel.impulse_key)
        self.assertTrue(panel.cas_impulse.isEnabled());self.assertTrue(panel.cas_definition.isEnabled())
        self.assertIn('Vista temporal no generada',panel.report.toPlainText())
        panel.reuse_button.menu().aboutToShow.emit()
        self.assertTrue(any(a.text()=='Respuesta al impulso h' for a in panel.reuse_button.menu().actions()))
        panel.start.setText('mal');panel.count.setText('65');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertIsNotNone(panel.impulse_key)

    def test_random_model_survives_optional_realization_errors(self):
        from signallab_pc.random_model_panel import RandomModelPanel
        panel=RandomModelPanel(self.host,'model');self.widgets.append(panel)
        panel.count.setText('-1');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertIsNotNone(panel.model);self.assertTrue(panel.records)
        self.assertIn('Realización no generada',panel.report.toPlainText())
        panel.count.setText('1024');panel.seed.setText('mal');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertIsNotNone(panel.model)



    def test_sampling_only_validates_controls_used_by_the_selected_operation(self):
        from signallab_pc.sampling_panel import SamplingPanel
        self.host.signal=Signal([1,2,3]);self.host._set_signal=lambda signal:setattr(self.host,'signal',signal)
        panel=SamplingPanel(self.host);self.widgets.append(panel)
        panel.rate_method.setCurrentIndex(1);panel.factor.setText('2');panel.phase.setText('mal')
        panel.change_rate();self.assertEqual(self.warnings,[])
        assert_allclose(self.host.signal.values,[1,0,2,0,3]);self.assertFalse(panel.phase.isEnabled())
        panel.rate_method.setCurrentIndex(0)
        with self.assertRaises(ValueError):panel.change_rate()
        from signallab_pc.rational_resampling_panel import RationalResamplingPanel
        rational=RationalResamplingPanel(self.host);self.widgets.append(rational)
        rational.source.set_source(Signal([1,2,3],metadata={'sample_rate_hz':10.,'time_start_s':2.}))
        rational.rate.setText('mal');rational.start.setText('mal');rational.up.setText('2');rational.down.setText('1')
        rational.calculate();self.assertEqual(self.warnings,[])
        self.assertEqual(rational.result.result.metadata['sample_rate_hz'],20.)
        self.assertEqual(rational.result.result.metadata['time_start_s'],2.)



    def test_statistics_survive_an_unavailable_histogram(self):
        from signallab_pc.random_panel import RandomPanel
        panel=RandomPanel(self.host,'statistics');self.widgets.append(panel)
        panel.source.set_source(Signal([1,2,3]))
        for bins in ['0','mal','1000000000000000']:
            panel.bins.setText(bins);panel.calculate()
            self.assertEqual(self.warnings,[])
            self.assertIn('Media real: 2.0',panel.report.toPlainText())
            self.assertIn('El resultado principal se conserva',panel.report.toPlainText())


    def test_bilateral_absolute_exponential_reuses_as_system_with_matching_frequency(self):
        panel=TransformLab(self.host,'z');self.widgets.append(panel)
        panel.expression.setText('2^(-abs(n))');panel.lower.setText('-oo');panel.upper.setText('oo');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertTrue(panel.last['evaluated']);panel.analyze_system.click()
        analysis=self.calculated_analysis();data=analysis.frequency_data
        assert_allclose(data.response,3/(5-4*np.cos(data.omega)),rtol=3e-12,atol=3e-12)

    def test_continuous_sinc_fourier_can_be_imported_inverted_and_reused(self):
        from signallab_pc.symbolic_fourier_panel import SymbolicFourierPanel
        from signallab_pc.result_expressions import expression_result
        from signallab_pc.cas_import import import_result
        from signallab_pc.cas_transfer import payload
        from signallab_pc.cas_engine import empty_state,restore
        from signallab_pc.symbolic import T
        panel=SymbolicFourierPanel(self.host);self.widgets.append(panel)
        panel.expression.setText('sin(t)/t');panel.calculate()
        self.assertEqual(self.warnings,[]);self.assertTrue(panel.last[1]['evaluated'])
        record=self.host.project.get(panel.last[0])
        imported=import_result(dict(payload=payload(record),state=empty_state(),cell=1))
        self.assertIsNotNone(restore(imported['encoded_value']))
        inverse=SymbolicFourierPanel(self.host,inverse=True);self.widgets.append(inverse)
        inverse.load_expression(expression_result(record),panel.last[0]);inverse.calculate()
        self.assertEqual(self.warnings,[]);self.assertTrue(inverse.last[1]['evaluated'])
        formula=restore(inverse.last[1]['cas_encoded'])
        self.assertAlmostEqual(complex(formula.subs(T,1).evalf()).real,float(np.sin(1)),places=12)

    def test_memoryless_equation_panels_ignore_unused_history_fields(self):
        from signallab_pc.difference_panel import DifferencePanel
        from signallab_pc.symbolic_panel import SymbolicPanel
        difference=DifferencePanel(self.host);self.widgets.append(difference)
        difference.coefficients.setText('2, 0');difference.expression.setText('1')
        difference.rest.setChecked(False);difference.initial.setText('mal');difference.calculate()
        self.assertEqual(self.warnings,[]);self.assertEqual(difference.result['result']['order'],0)
        self.assertFalse(difference.initial.isVisible())
        symbolic=SymbolicPanel(self.host);self.widgets.append(symbolic);symbolic.operation.setCurrentIndex(4)
        symbolic.coefficients.setText('2,0');symbolic.initial.setText('mal');symbolic.expression.setText('sin(t^2)');symbolic.calculate()
        self.assertEqual(self.warnings,[]);self.assertEqual(symbolic.result['result']['order'],0)
        self.assertIn('Sin',symbolic.result['result']['scope']);self.assertFalse(symbolic.initial.isVisible())

    def test_discrete_temporal_response_accepts_one_sample(self):
        from signallab_pc.temporal_panel import TemporalPanel
        panel=TemporalPanel(self.host);self.widgets.append(panel)
        panel.set_system(Transfer([2],[1]));panel.count.setText('1');panel.calculate()
        self.assertEqual(self.warnings,[])
        assert_allclose(panel.output.result.values,[2]);self.assertEqual(len(panel.output.result.values),1)


if __name__=='__main__':unittest.main()
