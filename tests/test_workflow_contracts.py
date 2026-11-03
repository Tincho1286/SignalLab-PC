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
        if self.current_operation not in self.pages:self.pages[self.current_operation]=SimpleNamespace(panel=SystemAnalysisPanel(self))
    def send_system(self,*args):raise AssertionError('An expression must not be converted before choosing analysis capabilities.')
    def choose_record(self,*args,**kwargs):return None


class WorkflowContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.host=Host();self.widgets=[];self.warnings=[]
        self.warning_patch=patch('PySide6.QtWidgets.QMessageBox.warning',side_effect=lambda *a:self.warnings.append(str(a[2])));self.warning_patch.start()
    def tearDown(self):
        self.warning_patch.stop()
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

    def test_rational_transfer_still_retains_numeric_system(self):
        from signallab_pc.result_expressions import ExpressionResult
        self.host.open_tool(ROUTES['system_analysis',0]);panel=self.host.pages[self.host.current_operation].panel
        panel.load_expression(ExpressionResult('z^2/(z-1/2)','z'));panel.count.setText('21');panel.calculate();self.assertEqual(self.warnings,[])
        self.assertIsInstance(panel.system,Transfer);self.assertEqual(panel.system.advance,1)
        z=np.exp(1j*panel.frequency_data.omega);assert_allclose(panel.frequency_data.response,z*z/(z-.5),atol=2e-13)
        self.assertTrue(panel.expression_actions.isHidden());self.assertTrue(panel.result_tabs.isTabVisible(2));self.assertFalse(panel.roc_choice.isHidden())


if __name__=='__main__':unittest.main()
