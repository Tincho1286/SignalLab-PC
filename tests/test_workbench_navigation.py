"""Keyboard, contextual help and editable realization workflows in Qt."""
from pathlib import Path
from unittest.mock import patch

import sympy as sp
from PySide6.QtCore import Qt, QUrl
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QComboBox, QDialog, QFileDialog, QInputDialog, QMessageBox, QWidget

from signallab_pc.catalog_delegate import TARGET
from signallab_pc.command_palette import TaskSearch
from signallab_pc.model import Signal
from signallab_pc.realization_editor import RealizationEditor
from signallab_pc.realization_graph import Block, LEFT_INPUT, LOWER_INPUT, RealizationGraph
from signallab_pc.symbolic import S, Z
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class WorkbenchNavigationContracts(DesktopSessionFixture):
    def test_returning_to_tools_keeps_the_draft_without_preparing_the_workspace_again(self):
        window = self.window()
        window.show()
        dft = ROUTES['basic', 'dft']
        inverse = ROUTES['basic', 'idft']
        other = ROUTES['estimation', 'kalman']
        with patch.object(window, '_configure_readable_layouts', wraps=window._configure_readable_layouts) as prepare:
            window.open_tool(dft)
            page = window.pages[dft]
            page.first.expression.setText('3*n-2')
            window.open_tool(inverse)
            window.open_tool(other)
            self.assertEqual([call.args[0].tool_item for call in prepare.call_args_list], [dft, inverse, other])
            window.open_tool(dft)
            window.show_area('spectra')
            window.open_tool(other)
            window.open_tool(dft)
            self.assertEqual(prepare.call_count, 3)
        self.assertIs(window.pages[dft], page)
        self.assertEqual(page.first.expression.text(), '3*n-2')
        self.assertIs(window.current_calculate.window(), window)

    def choose(self, window, query, target):
        def keyboard_select(dialog):
            expected_row = next(index for index in range(dialog.list.count())
                                if dialog.list.item(index).data(TARGET) == target)
            for _ in range(dialog.list.count()):
                if dialog.list.currentRow() == expected_row:
                    break
                QTest.keyClick(dialog.query, Qt.Key.Key_Down)
            self.assertEqual(dialog.list.currentRow(), expected_row)
            QTest.keyClick(dialog.query, Qt.Key.Key_Return)
            return dialog.result()

        with patch.object(TaskSearch, 'exec', keyboard_select):
            window.focus_tool_search(query)

    def test_command_search_selects_inverse_bilateral_laplace_and_returns_from_help(self):
        window = self.window()
        window.show()
        key = ('transform_lab', 'laplace')
        route = ROUTES[key]
        self.choose(window, 'Laplace inversa bilateral', ('tool', key, (('interpretation', 1), ('mode', 1))))
        self.assertEqual(window.current_operation, route)
        page = window.pages[route]
        self.assertEqual(page.panel.mode.currentIndex(), 1)
        self.assertEqual(page.panel.interpretation.currentIndex(), 1)
        window.open_help()
        library = window.pages['menu', 'Biblioteca']
        self.assertEqual(library.return_route, route)
        self.assertEqual(library.guide_context.label, 'Inversa · Bilateral')
        self.assertIn('franja de convergencia', library.guide_context.instructions)
        self.assertIn('franja de convergencia', library.text.toPlainText())
        library.return_button.click()
        self.assertEqual(window.current_operation, route)
        self.assertIs(window.pages[route], page)

    def test_favorites_persist_and_search_returns_to_existing_documents_and_results(self):
        window = self.window()
        window.show()
        route = ROUTES['basic', 'dft']
        window.open_tool(route)
        window.favorite_action.click()
        self.assertTrue(window.favorite_action.isChecked())
        self.assertIn(('basic', 'dft'), window.favorite_tools)
        record = window.publish(Signal([3, 42], name='Temperatura nocturna'), operation='Termómetro')
        self.choose(window, 'Temperatura nocturna', ('result', record))
        self.assertEqual(window.visible_records[window.project_list.currentRow()]['id'], record)
        self.choose(window, '', ('tool', ('basic', 'dft')))
        self.assertEqual(window.current_operation, route)
        another = self.window()
        self.assertIn(('basic', 'dft'), another.favorite_tools)
        window.favorite_action.click()
        self.assertFalse(window.favorite_action.isChecked())
        window.show_home()
        document = next(window.documents.tabData(i) for i in range(window.documents.count())
                        if window.documents.tabData(i) and window.documents.tabData(i)[1:2] == ('workspace',))
        self.choose(window, '', ('document', document))
        self.assertEqual(window.current_operation, route)
        dialog = TaskSearch(window, 'zzqv-unmatched')
        self.addCleanup(dialog.deleteLater)
        self.assertEqual(dialog.list.count(), 0)
        self.assertIn('No hay coincidencias', dialog.note.text())
        QTest.keyClick(dialog.query, Qt.Key.Key_Return)
        self.assertIsNone(dialog.selection)

    def test_help_changes_with_input_convention_after_switching_tool_modes(self):
        window = self.window()
        window.show()
        for key, settings, label, phrase in [
            (('transform_lab', 'z'), (('mode', 0), ('direct_input', 1)), 'Secuencia finita', 'cada muestra'),
            (('transform_lab', 'z'), (('mode', 1),), 'Inversa', 'secuencia completa'),
            (('system_analysis', 0), (('domain', 1), ('definition_mode', 0)), 'H(z)', 'z⁻¹'),
            (('system_analysis', 0), (('domain', 0), ('definition_mode', 1)), 'H(s)', 'parámetros'),
            (('system_analysis', 0), (('definition_mode', 3),), 'Diagrama', 'sumadores'),
            (('systems', 9), (('domain', 1), ('stimulus', 1)), 'H(z)', 'muestra unitaria'),
            (('systems', 9), (('domain', 0), ('stimulus', 2)), 'H(s)', 'entrada propia'),
            (('course_tools', 'fir'), (), 'FIR', 'rad/muestra'),
            (('course_tools', 'iir'), (), 'IIR digital', 'rad/muestra'),
            (('course_tools', 'analog'), (), 'IIR analógico', 'rad/s'),
        ]:
            with self.subTest(key=key, settings=settings):
                window.open_tool_search(key, settings)
                route = ROUTES[key]
                self.assertEqual(window.current_operation, route)
                window.open_help()
                library = window.pages['menu', 'Biblioteca']
                self.assertIn(label, library.guide_context.label)
                self.assertIn(phrase, library.guide_context.instructions)
                self.assertEqual(library.return_route, route)

    def test_result_links_preserve_the_filter_surface_and_restore_the_selected_detail_tab(self):
        window = self.window()
        window.show()
        parent = window.publish(Signal([4,7],-1,name='Registro bruto'), operation='Entrada: medición')
        child = window.publish(Signal([8,14],-1,name='Registro calibrado'), operation='Calibración',
                               parents=[parent])
        window.focus_result(child)
        browser = window.pages['menu','Proyecto']
        window.include_inputs.setChecked(False)
        window.result_search.setText('calibrado')
        self.assertEqual([record['id'] for record in window.visible_records], [child])
        browser.detail_tabs.setCurrentIndex(browser.links_index)
        browser.open_link(QUrl(f'result:{browser.link_ids.index(parent)}'))
        self.assertEqual(browser.active_record['id'], parent)
        self.assertEqual(window.result_search.text(), 'calibrado')
        self.assertIn('1 vinculado', window.result_count.text())
        self.assertIn('vínculo', window.project_list.currentItem().toolTip())
        browser.follow_back()
        self.assertEqual(browser.active_record['id'], child)
        self.assertEqual(browser.detail_tabs.currentIndex(),browser.links_index)
        browser.open_link(QUrl('result:999'))
        self.assertEqual(browser.active_record['id'], child)
        window.result_search.setText('inexistente')
        self.assertIsNone(browser.active_record)
        self.assertEqual(window.result_count.text(), '0 resultados')

    def test_shortcuts_keep_the_input_focus_and_reopen_closed_documents_with_their_drafts(self):
        window = self.window()
        window.resize(850,650)
        window.show()
        key = ('basic','generate')
        route = ROUTES[key]
        window.open_tool(route)
        page = window.pages[route]
        source = page.first
        input_field = source.expression.field
        source.expression.setText('3*n-2')
        source.count.setText('5')
        window.desktop_keys.reveal(input_field)
        self.app.processEvents()
        self.assertIs(QWidget.window(input_field),window)
        window.calculate_active()
        self.wait_for_calculation(window)
        shortcuts = window.desktop_keys
        shortcuts.focus_surface(False)
        self.assertIs(self.app.focusWidget(), input_field)
        shortcuts.focus_surface(True)
        self.assertTrue(page.workspace.results.isAncestorOf(self.app.focusWidget()))
        shortcuts.toggle_output()
        self.assertTrue(page.workspace.output_expanded)
        shortcuts.toggle_output()
        self.assertFalse(page.workspace.output_expanded)
        before = window.documents.count()
        shortcuts.close_document()
        self.assertEqual(window.documents.count(), before-1)
        window.open_tool(route)
        self.assertEqual(window.documents.count(), before)
        self.assertIs(window.pages[route], page)
        self.assertEqual(page.first.expression.text(), '3*n-2')


class RealizationEditorContracts(DesktopSessionFixture):
    def editor(self, graph):
        window = self.window()
        editor = RealizationEditor(graph, window, owner=window)
        editor.show()
        self.app.processEvents()
        self.addCleanup(editor.close)
        return editor

    def drag_wire(self, editor, source, target, index=LEFT_INPUT):
        view = editor.view
        start = view.mapFromScene(editor.blocks[source].output.scenePos())
        finish = view.mapFromScene(editor.blocks[target].inputs[index].scenePos())
        QTest.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(view.viewport(), finish)
        self.assertIsNotNone(view.cable_preview)
        QTest.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=finish)

    def test_dragged_ports_compute_a_feedback_transfer_and_validate_loop_sign(self):
        graph = RealizationGraph('analog',
                                 (Block(1, 'input', 0, 0), Block(2, 'output', 580, 0),
                                  Block(3, 'transfer', 145, 0, formula='1/(s+1)'), Block(4, 'sum', 380, 0)), ())
        editor = self.editor(graph)
        for source, target, index in [(1, 3, LEFT_INPUT), (3, 4, LEFT_INPUT),
                                      (4, 4, LOWER_INPUT), (4, 2, LEFT_INPUT)]:
            self.drag_wire(editor, source, target, index)
        self.assertTrue(editor.connection_state.property('complete'))
        self.assertEqual(sp.cancel(editor.graph().transfer()-1/(2*(1+S))), 0)
        editor.editor_tabs.setCurrentIndex(1)
        self.assertIn('Y(s)', editor.equations_view.toPlainText())
        self.assertFalse(editor.equations_dirty)
        editor.editor_tabs.setCurrentIndex(0)
        def change_lower_sign(dialog):
            dialog.findChildren(QComboBox)[1].setCurrentIndex(0)
            return QDialog.DialogCode.Accepted

        with patch.object(QDialog, 'exec', change_lower_sign):
            editor.edit_block(editor.blocks[4])
        self.assertEqual(editor.blocks[4].block.input_signs, (1, 1))
        with self.assertRaisesRegex(ValueError, 'lazo|singular|determina'):
            editor.graph().transfer()
        before = editor.graph()
        self.drag_wire(editor, 1, 3)
        self.assertEqual(editor.graph(), before)

    def test_edit_reset_and_reopen_a_discrete_diagram_without_losing_gain_or_delay(self):
        editor = self.editor(RealizationGraph.empty('digital'))
        with patch.object(QInputDialog, 'getText', return_value=('1/3', True)):
            editor.palette_buttons[1].click()
        editor.memory.click()
        self.assertIn('z⁻¹', editor.memory.text())
        editor.resize(580, 400)
        editor.fit_diagram()
        before = editor.view.transform().m11()
        editor.change_zoom(1.15)
        self.assertGreater(editor.view.transform().m11(), before)
        self.assertFalse(editor.fit_mode)
        editor.fit_diagram()
        for source, target in [(1, 3), (3, 4), (4, 2)]:
            editor.connect_button.click()
            editor.connect_block(editor.blocks[source])
            editor.connect_block(editor.blocks[target])
        graph = editor.graph()
        self.assertEqual(sp.cancel(graph.transfer()-1/(3*Z)), 0)
        path = self.path/'diagrama'
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(path), '')):
            editor.save_file()
        stored = path.with_suffix('.json')
        self.assertTrue(stored.exists())
        editor.scene.clearSelection()
        editor.blocks[3].setSelected(True)
        editor.delete_selection()
        self.assertFalse(editor.connection_state.property('complete'))
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(stored), '')):
            self.question.return_value = QMessageBox.StandardButton.No
            editor.open_file()
            self.assertNotIn(3, editor.blocks)
            self.question.return_value = QMessageBox.StandardButton.Yes
            editor.open_file()
        self.assertEqual(editor.graph(), graph)
        invalid = Path(self.path/'invalid.json')
        invalid.write_text('{}', encoding='utf-8')
        with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(invalid), '')):
            editor.open_file()
        self.warning.assert_called_once()
        self.assertEqual(editor.graph(), graph)
        editor.new_diagram()
        self.assertEqual(editor.graph(), RealizationGraph.empty('digital'))
