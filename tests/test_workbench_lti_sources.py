"""Select a transfer from Results and distinguish its exact source and model."""
from unittest.mock import patch

import numpy as np
from PySide6.QtWidgets import QDialog, QFileDialog

from signallab_pc.filters import Transfer
from signallab_pc.project_picker import ProjectPicker
from signallab_pc.result_expressions import ExpressionResult
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class LtiSourceContracts(DesktopSessionFixture):
    def test_reopen_coefficient_view_with_exact_parent_and_imported_clock(self):
        window = self.window()
        route = ROUTES['system_analysis',0]
        window.open_tool(route)
        panel = window.pages[route].panel
        definitions = [
            ({'operation':'system_formula','expression':'1/(1-(1/3)/z)','domain':'digital'},1),
            ({'operation':'system_analysis','b':['1'],'a':['1','-1/3'],'domain':'digital'},0),
        ]
        for index,(request,mode) in enumerate(definitions):
            with self.subTest(mode=mode):
                parent = window.project.add({'request':request,'result':{'result':'1/(1-(1/3)/z)'}})
                model = Transfer([1],[1,-1/3],name=f'Reutilizable {index}',sample_period_s=0.25)
                key = window.publish(model,operation='Modelo digital',parents=[parent])
                with patch.object(window,'choose_record',return_value=key):
                    panel.choose()
                self.assertEqual(panel.definition_mode.currentIndex(),mode)
                self.assertEqual(panel.input_id,key)
                if mode:
                    self.assertEqual(panel.transfer_formula.text(),request['expression'])
                else:
                    self.assertEqual(panel.a.text(),'1, -1/3')
                window.calculate_active()
                self.wait_for_calculation(window,12000)
                self.assertIsNotNone(panel.analyzed_system)
                frequency = np.array([0.15,np.pi/3,1.9])
                np.testing.assert_allclose(panel.analyzed_system.response(frequency),
                                           1/(1-np.exp(-1j*frequency)/3),rtol=1e-14)
                self.assertEqual(panel.analyzed_system.sample_period_s,0.25)
                if mode:
                    panel.transfer_formula.setText('1/(1-(1/2)/z)')
                else:
                    panel.a.setText('1, -1/2')
                window.calculate_active()
                self.wait_for_calculation(window,12000)
                self.assertIsNone(panel.analyzed_system.sample_period_s)
                np.testing.assert_allclose(panel.analyzed_system.response(frequency),
                                           1/(1-np.exp(-1j*frequency)/2),rtol=1e-14)

    def test_incompatible_frequency_units_preserve_draft_and_expression_is_exportable(self):
        window = self.window()
        route = ROUTES['system_analysis',0]
        window.open_tool(route)
        panel = window.pages[route].panel
        original = panel.transfer_formula.text()
        with self.assertRaisesRegex(ValueError,'unidad de frecuencia única'):
            panel.load_expression(ExpressionResult('exp(-i*w)','w',units='Hz'))
        self.assertEqual(original,panel.transfer_formula.text())
        panel.load_expression(ExpressionResult('exp(-i*w)','w',units='rad/muestra'))
        window.calculate_active()
        self.wait_for_calculation(window,12000)
        self.assertIsNotNone(panel._definition_id)
        expression = window.project.expression(panel._definition_id)
        self.assertEqual((expression.variable,expression.units),('w','rad/muestra'))
        np.testing.assert_allclose(panel.frequency_data.magnitude,1,atol=1e-12)
        with patch.object(QFileDialog,'getSaveFileName',return_value=('','')):
            panel.export_expression()
        path = self.path/'delay.json'
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(path),'')):
            panel.export_expression()
        self.assertTrue(path.is_file())
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'')):
            picker = ProjectPicker(window,'expression',variables=['w'],units=['rad/muestra'])
            picker.import_button.click()
        self.assertEqual(picker.result(),QDialog.DialogCode.Accepted)
        exported = window.project.expression(picker.selected_id)
        self.assertEqual(exported,expression)
