"""Worksheet keyboard, typed results, cancellation and reuse through Qt."""
from threading import Event
from unittest.mock import patch

import numpy as np
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QInputDialog, QMessageBox
import sympy as sp

from signallab_pc.cas_engine import restore
from signallab_pc.cas_reference import CAS_ROUTE
from signallab_pc.cas_transfer import send_to_cas
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class WorksheetControlContracts(DesktopSessionFixture):
    def worksheet(self):
        window = self.window()
        window.open_cas()
        return window,window.pages[CAS_ROUTE]

    def evaluation(self, window, sheet, expression):
        sheet.input.setPlainText(expression)
        QTest.keyClick(sheet.input,Qt.Key.Key_Return)
        self.wait_for_calculation(window,timeout_ms=12000)
        entry = sheet.entries[-1]
        self.assertEqual(entry['status'],'done',entry.get('error'))
        return restore(sheet.state['results'][str(entry['cell'])])

    def test_command_palette_keyboard_history_and_new_sheet_restore_the_right_draft(self):
        window,sheet = self.worksheet()
        sheet.calculate()
        QTest.keyClick(sheet.input,Qt.Key.Key_Up,Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(sheet.entries,[])
        sheet.input.setPlainText('2+3')
        sheet.input.selectAll()
        sheet.command_button.click()
        dialog = sheet.command_dialog
        dialog.search.setText('unavailable-test-operator')
        self.assertFalse(dialog.insert_button.isEnabled())
        dialog.search.setText('simplificar')
        dialog.insert_button.click()
        self.assertEqual(sheet.input.toPlainText(),'simplify(2+3)')
        QTest.keyClick(sheet.input,Qt.Key.Key_Return)
        self.wait_for_calculation(window,timeout_ms=12000)
        self.assertEqual(restore(sheet.state['results']['1']),5)
        sheet.command_button.click()
        self.assertIs(sheet.command_dialog,dialog)
        dialog.close()

        sheet.input.setPlainText('integrate(x,')
        sheet.input.moveCursor(QTextCursor.MoveOperation.End)
        QTest.keyClick(sheet.input,Qt.Key.Key_Return,Qt.KeyboardModifier.ShiftModifier)
        multiline = sheet.input.toPlainText()
        self.assertIn('\n',multiline)
        self.assertEqual(len(sheet.entries),1)
        QTest.keyClick(sheet.input,Qt.Key.Key_Up,Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(sheet.input.toPlainText(),'simplify(2+3)')
        QTest.keyClick(sheet.input,Qt.Key.Key_Down,Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(sheet.input.toPlainText(),multiline)
        sheet.follow_link(QUrl('cas-input:1'))
        self.assertEqual(sheet.input.toPlainText(),'simplify(2+3)')
        sheet.input.clear()
        sheet.follow_link(QUrl('cas-result:1'))
        self.assertEqual(sheet.input.toPlainText(),'r1')
        sheet.follow_link(QUrl('cas-view:1'))
        self.assertEqual(len(sheet.formula_dialogs),1)
        sheet.formula_dialogs[-1].close()
        self.assertEqual(sheet.formula_dialogs,[])
        sheet.copy_result()
        self.assertEqual(QApplication.clipboard().text(),'5')
        sheet.check_pending()
        self.assertTrue(sheet.new_button.isEnabled())
        self.question.return_value = QMessageBox.StandardButton.Cancel
        sheet.new_button.trigger()
        self.assertEqual(len(sheet.entries),1)
        records = window.project.headers()
        self.question.return_value = QMessageBox.StandardButton.Yes
        sheet.new_button.trigger()
        self.assertEqual(sheet.session_snapshot()['draft'],'')
        self.assertEqual(sheet.entries,[])
        self.assertIsNone(sheet.state['ans'])
        self.assertEqual(window.project.headers(),records)

    def test_typed_mapping_import_preserves_values_and_rejects_colliding_labels(self):
        window,sheet = self.worksheet()
        data = {'matriz': {'shape':[2,2],'dtype':'complex128',
                           'values':[[1,1],[2,0],[0,3],[4,0]]},
                'piso': {'nonfinite':'-infinity'},
                'coeficiente': {'real':3,'imag':-2},
                'enumeración': [4,{'real':1,'imag':1}]}
        key = window.publish({'report':'Matriz de coeficientes', 'calculated_data':data})
        send_to_cas(window,key)
        self.wait_for_calculation(window,timeout_ms=12000)
        result_id = sheet.selected_entry()['result_id']
        value = restore(sheet.state['results']['1'])
        self.assertEqual(value[sp.Symbol('piso')],-sp.oo)
        self.assertEqual(value[sp.Symbol('coeficiente')],3-2*sp.I)
        self.assertEqual(value[sp.Symbol('matriz')],sp.Matrix([[1+sp.I,2],[3*sp.I,4]]))
        self.assertEqual(self.evaluation(window,sheet,'r1[matriz][1,0] + r1[coeficiente]'),3+sp.I)
        records = {row['id']:row for row in window.project.headers()}
        self.assertEqual(records[result_id]['parents'],[key])
        self.assertEqual(records[sheet.selected_entry()['result_id']]['parents'],[result_id])
        preserved = sheet.state
        before = window.project.headers()
        send_to_cas(window,value={'R-A':1,'R+A':2})
        self.wait_for_calculation(window,timeout_ms=12000)
        self.assertEqual(sheet.entries[-1]['status'],'error')
        self.assertIn('coinciden como R_A',sheet.entries[-1]['error'])
        self.assertIs(sheet.state,preserved)
        self.assertEqual(window.project.headers(),before)

    def test_cancelled_cell_keeps_last_exact_result_and_allows_recovery(self):
        window,sheet = self.worksheet()
        self.assertEqual(self.evaluation(window,sheet,'a:=2/3'),sp.Rational(2,3))
        started,release = Event(),Event()
        preserved = sheet.state
        before = window.project.headers()

        def pending(_request):
            started.set()
            if not release.wait(8):
                raise TimeoutError('Worksheet cancellation was not delivered.')
            return {'error':'Terminado después de la cancelación'}

        with patch('signallab_pc.cas_panel.run_request',side_effect=pending):
            sheet.input.setPlainText('r1^5')
            sheet.calculate()
            try:
                self.assertTrue(started.wait(4))
                sheet.input.setPlainText('r1+1')
                sheet.calculate()
                self.assertEqual(len(sheet.entries),2)
                self.assertEqual(len(sheet.session_snapshot()['entries']),1)
                sheet.new_sheet()
                self.assertEqual(len(sheet.entries),2)
                window.cancel_button.click()
            finally:
                release.set()
            self.wait_for_calculation(window,timeout_ms=12000)
        sheet.check_pending()
        self.assertEqual(sheet.entries[-1]['status'],'error')
        self.assertIn('Cálculo detenido',sheet.entries[-1]['error'])
        self.assertEqual(window.project.headers(),before)
        self.assertIs(sheet.state,preserved)
        self.assertEqual(self.evaluation(window,sheet,'r1+1'),sp.Rational(5,3))

    def test_frequency_reuse_waits_for_units_and_keeps_the_selected_result(self):
        window,sheet = self.worksheet()
        self.evaluation(window,sheet,'1+exp(-i*w)')
        key = sheet.selected_entry()['result_id']
        with patch.object(QInputDialog,'getItem',return_value=('',False)):
            sheet.send_result('frequency')
        self.assertEqual(window.current_operation,CAS_ROUTE)
        self.assertEqual(sheet.selected_entry()['result_id'],key)
        with patch.object(QInputDialog,'getItem',return_value=('rad/muestra',True)):
            sheet.send_result('frequency')
        route = ROUTES['system_analysis',0]
        self.assertEqual(window.current_operation,route)
        panel = window.pages[route].panel
        panel.count.setText('17')
        window.calculate_active()
        self.wait_for_calculation(window,timeout_ms=12000)
        data = panel.frequency_data
        self.assertEqual(data.units,'rad/muestra')
        np.testing.assert_allclose(data.response,1+np.exp(-1j*data.omega),atol=1e-13)
