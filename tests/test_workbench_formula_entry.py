"""Test student-facing formula menus and spreadsheet-style coefficient entry."""
from unittest.mock import patch

import numpy as np
from PySide6.QtCore import Qt, QItemSelection, QItemSelectionModel
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QInputDialog, QPushButton

from signallab_pc.matrix_editor import MatrixEditor
from signallab_pc.state_space_panel import matrix
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class FormulaEntryContracts(DesktopSessionFixture):
    def test_coefficient_table_preserves_powers_and_recovers_after_zero_denominator(self):
        window = self.window()
        route = ROUTES['system_analysis',0]
        window.open_tool(route)
        panel = window.pages[route].panel
        panel.domain.setCurrentIndex(1)
        panel.b.setText('1')
        panel.b.remove_term()
        panel.b.add_term()
        model = panel.b.model
        self.assertEqual(model.data(model.index(1,0)),'z⁻¹')
        self.assertFalse(model.setData(model.index(1,0),'pi'))
        self.assertTrue(model.setData(model.index(1,1),'pi'))
        panel.a.setText('0, 0')
        panel.transfer_preview.refresh()
        self.assertIn('denominador no puede ser cero',panel.transfer_preview.toPlainText())
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertIsNone(panel.analyzed_system)
        self.assertEqual(window.project.headers(),[])
        panel.a.setText('1, -10^(-3)')
        panel.transfer_preview.refresh()
        window.calculate_active()
        self.wait_for_calculation(window,12000)
        angles = np.array([0.1,0.5,np.pi])
        expected = (1+np.pi*np.exp(-1j*angles))/(1-0.001*np.exp(-1j*angles))
        np.testing.assert_allclose(panel.analyzed_system.response(angles),expected,rtol=1e-14)

    def test_piecewise_conditions_helpers_preserve_order_and_calculable_values(self):
        window = self.window()
        route = ROUTES['basic','generate']
        window.open_tool(route)
        page = window.pages[route]
        field = page.first
        editor = field.expression
        editor.setText('2*n')
        editor.mode.setCurrentIndex(1)
        editor.table.setCurrentCell(0,1)
        editor.prepare_functions()
        conditions = next(action.menu() for action in editor.functions_menu.actions() if action.menu())
        next(action for action in conditions.actions() if action.text()=='n == 0').trigger()
        self.assertEqual(editor.table.item(0,1).text(),'n == 0')
        editor.table.item(0,0).setText('5')
        editor.other.setText('-n')
        next(button for button in editor.findChildren(QPushButton) if button.text()=='+ Tramo').click()
        editor.table.item(1,0).setText('2*n')
        editor.mode.setCurrentIndex(0)
        original = editor.text()
        with patch.object(QInputDialog,'getText',return_value=('n',False)):
            editor.replace_button.click()
        self.assertEqual(editor.text(),original)
        field.origin.setText('-2')
        field.count.setText('5')
        window.calculate_active()
        self.wait_for_calculation(window)
        np.testing.assert_array_equal(page.basic_result.result.values,[2,1,5,2,4])

    def test_formula_menu_inserts_discrete_impulse_and_opens_its_reference(self):
        window = self.window()
        route = ROUTES['basic','generate']
        window.open_tool(route)
        page = window.pages[route]
        field = page.first
        editor = field.expression
        editor.setText('')
        editor.prepare_functions()
        actions = editor.functions_menu.actions()
        periodic = next(action.menu() for action in actions if action.text()=='Señales periódicas')
        self.assertIn('ImpulseTrain(n, 2)',[action.text() for action in periodic.actions()])
        next(action for action in actions if action.text().startswith('Impulso  ·')).trigger()
        self.assertEqual(editor.text(),'Impulse(n)')
        field.origin.setText('-1')
        field.count.setText('3')
        window.calculate_active()
        self.wait_for_calculation(window)
        np.testing.assert_array_equal(page.basic_result.result.values,[0,1,0])
        next(action for action in actions if action.text()=='Sintaxis y argumentos…').trigger()
        library = window.pages['menu','Biblioteca']
        self.assertIn('Guía de funciones',library.text.toPlainText())

    def test_matrix_copy_paste_preserves_complex_and_scientific_coefficients(self):
        clipboard = self.app.clipboard()
        saved = clipboard.text()
        self.addCleanup(clipboard.setText,saved)
        editor = MatrixEditor('1, 0; 0, 1')
        self.addCleanup(editor.deleteLater)
        editor.table.setCurrentIndex(editor.model.index(0,1))
        modifier = Qt.KeyboardModifier.ControlModifier

        clipboard.setText('4\t7\n1')
        QTest.keyClick(editor.table,Qt.Key.Key_V,modifier)
        self.assertIn('igual cantidad de columnas',self.warning.call_args.args[-1])
        self.assertEqual(editor.text(),'1, 0; 0, 1')
        clipboard.setText('pi\t10^(-3)\n-2\t1+2i')
        QTest.keyClick(editor.table,Qt.Key.Key_V,modifier)
        np.testing.assert_allclose(matrix(editor.text()),[[1,np.pi,0.001],[0,-2,1+2j]],rtol=1e-14)

        selected = QItemSelection(editor.model.index(0,1),editor.model.index(1,2))
        editor.table.selectionModel().select(selected,QItemSelectionModel.SelectionFlag.ClearAndSelect)
        QTest.keyClick(editor.table,Qt.Key.Key_C,modifier)
        self.assertEqual(clipboard.text(),'pi\t10^(-3)\n-2\t1+2i')
        editor.columns.setValue(2)
        editor.columns.setValue(3)
        np.testing.assert_allclose(matrix(editor.text()),[[1,np.pi,0.001],[0,-2,1+2j]],rtol=1e-14)
