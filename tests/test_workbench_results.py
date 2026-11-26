"""Scientific results exercised through the production workbench."""
from unittest.mock import patch

import numpy as np
from PySide6.QtWidgets import QInputDialog, QMenu, QPushButton

from signallab_pc.filters import Transfer
from signallab_pc.model import Signal
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class WorkbenchResultContracts(DesktopSessionFixture):
    def test_different_cursor_readings_open_the_corresponding_rows_without_losing_alignment(self):
        window=self.window()
        window.show()
        route=ROUTES['basic','generate']
        window.open_tool(route)
        view=window.pages[route].basic_result
        signal=Signal([1,2,8,4,9j],-2,name='Serie de medición')
        view.show_result(signal)
        view.table_view.set_signals([signal])
        table=view.table_view
        table.select_cell(2,1)
        table.show_in_figure()
        probe=view.canvas._signallab_probe
        trace=next(trace for trace in probe.traces if trace.sample_source and trace.sample_source[1]=='real')
        probe.focus(trace,-1,'a')
        probe.focus(trace,2,'b')
        rows=probe.available_value_rows(table)
        self.assertEqual({row[2] for row in rows}, {1,2,4})
        probe.copy_values()
        copied=self.app.clipboard().text().splitlines()
        self.assertGreaterEqual(len(copied),2)
        self.assertIn('A',copied[0])
        self.assertIn('B',copied[0])
        class DismissedMenu(QMenu):
            def exec(self, position):
                return None

        class CursorBMenu(QMenu):
            def exec(self, position):
                return next(item for item in self.actions() if item.text().startswith('Cursor B'))

        with patch('signallab_pc.plot_probe.QMenu',DismissedMenu):
            probe.open_values()
        self.assertEqual(table.table.currentIndex().row(),2)
        with patch('signallab_pc.plot_probe.QMenu',CursorBMenu):
            probe.open_values()
        self.assertEqual(table.table.currentIndex().row(),4)
        self.assertEqual(table.model.coordinate(4),2)
        self.assertEqual(probe.a[trace.key],(-1,2))
        self.assertEqual(probe.b[trace.key],(2,0))

    def test_library_dft_and_idft_preserve_phase_origin_and_input_navigation(self):
        window=self.window()
        window.show()
        source=Signal([2-1j,3j,-.5],-4,name='Medición',metadata={'sample_rate_hz':64})
        key=window.publish(source,operation='Registro instrumentado')
        window.focus_result(key)
        window.prepare_selected_reuse()
        next(action for action in window.reuse_actions if action.text().endswith('Directa · Transformada')).trigger()
        page=window.pages[ROUTES['basic','dft']]
        self.assertEqual(page.first.reference_id,key)
        self.assertIsNotNone(page.workspace.handoff)
        window.calculate_active()
        self.wait_for_calculation(window)
        record=window.project.headers('signal')[-1]
        self.assertEqual(record['parents'],[key])
        spectrum=window.project.get(record['id'])
        expected=[sum(x*np.exp(-1j*w*n) for n,x in zip(range(-4,-1),source.values))
                  for w in spectrum.axis]
        np.testing.assert_allclose(spectrum.values,expected,atol=1e-13)
        back=next(b for b in page.workspace.handoff.findChildren(QPushButton) if 'origen' in b.text())
        back.click()
        self.assertEqual(window.visible_records[window.project_list.currentRow()]['id'],key)
        window.focus_result(record['id'])
        window.prepare_selected_reuse()
        next(action for action in window.reuse_actions
             if action.text().startswith('DFT / FFT') and 'Inversa' in action.text()).trigger()
        inverse=window.pages[ROUTES['basic','idft']]
        self.assertEqual(inverse.first.reference_id,record['id'])
        window.calculate_active()
        self.wait_for_calculation(window)
        reconstructed=window.project.headers('signal')[-1]
        recovered=window.project.get(reconstructed['id'])
        self.assertEqual(reconstructed['parents'],[record['id']])
        self.assertEqual(recovered.origin,source.origin)
        self.assertEqual(recovered.metadata['sample_rate_hz'],64)
        np.testing.assert_allclose(recovered.values,source.values,atol=1e-13)

    def test_declining_two_input_handoff_preserves_library_selection_and_drafts(self):
        window=self.window()
        source=Signal([2+1j,5,7],-2,name='Registro')
        other=Signal([3,4],-1,name='Ventana')
        key=window.publish(source,operation='Registro')
        other_key=window.publish(other,operation='Ventana')
        route=ROUTES['signal_product',0]
        window.open_tool(route)
        panel=window.pages[route].panel
        panel.second.set_source(other,other_key)
        window.focus_result(key)
        with patch.object(QInputDialog,'getItem',return_value=('',False)) as chooser:
            window.send_signal(source,key,route)
        self.assertTrue(chooser.called)
        self.assertEqual(window.visible_records[window.project_list.currentRow()]['id'],key)
        self.assertEqual(panel.second.reference_id,other_key)
        with patch.object(QInputDialog,'getItem',side_effect=lambda *args:(args[3][0],True)):
            window.send_signal(source,key,route)
        self.assertEqual(panel.first.reference_id,key)
        self.assertEqual(panel.second.reference_id,other_key)
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertEqual(panel.result.origin,-2)
        np.testing.assert_array_equal(panel.result.values,[0,15,28])
        parents=window.project.headers('signal')[-1]['parents']
        self.assertEqual(parents,[key,other_key])

    def test_two_system_handoff_retains_provenance_and_returns_the_cascade(self):
        window=self.window()
        r=ROUTES['interconnection',0]
        systems=[Transfer([1],[1,-.5],sample_period_s=.01),Transfer([3,1],[1],sample_period_s=.01)]
        keys=[window.publish(h,operation='Sistema ingresado') for h in systems]
        for index,h in enumerate(systems):
            window.focus_result(keys[index])
            with patch.object(QInputDialog,'getItem',side_effect=lambda *args:(args[3][index],True)):
                window.send_system(h,keys[index],r)
        page=window.pages[r]
        self.assertEqual(page.panel.parents,keys)
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertIsNotNone(page.panel.result)
        result=page.panel.result
        assert result is not None
        self.assertEqual(result.sample_period_s,.01)
        q=np.exp(-1j*np.array([0,.1,2.5,np.pi]))
        np.testing.assert_allclose(result.response([0,.1,2.5,np.pi]),(3+q)/(1-.5*q),atol=1e-14)

    def test_finite_z_fir_window_and_sample_editor_read_the_same_source(self):
        window=self.window()
        source=Signal([2+1j,3,4],-1,name='Entrada')
        key=window.publish(source,operation='Entrada inicial')
        for route in (ROUTES['transform_lab','z'],ROUTES['fir_window',0],ROUTES['signal_editor',0]):
            window.focus_result(key)
            window.send_signal(source,key,route)
            page=window.pages[route]
            self.assertEqual(window.current_operation,route)
            if route[1]=='transform_lab':
                field=page.panel.source
            elif route[1]=='fir_window':
                field=page.panel.h
            else:
                self.assertEqual(page.panel.parent_id,key)
                np.testing.assert_array_equal(page.panel.current.values,source.values)
                continue
            self.assertEqual(field.reference_id,key)
            self.assertEqual(field.read().origin,-1)
            np.testing.assert_array_equal(field.read().values,source.values)
        self.assertEqual(len(window.project.headers()),1)

    def test_answer_reuse_in_cas_keeps_the_original_expression_id(self):
        from signallab_pc.cas_panel import CAS_ROUTE
        window=self.window()
        key=window.publish({'request':{'operation':'z_expression','expression':'n'},
                            'result':{'result':'z**2+1','evaluated':True,'output_variable':'z'}},
                           title='Expresión para reutilizar')
        window.focus_result(key)
        window.prepare_selected_reuse()
        action=next(a for a in window.reuse_actions if 'CAS' in a.text())
        action.trigger()
        # This handoff starts an instrumented, fresh Python CAS worker.
        self.wait_for_calculation(window, timeout_ms=12_000)
        self.assertEqual(window.current_operation,CAS_ROUTE)
        panel=window.pages[CAS_ROUTE]
        self.assertEqual(panel.entries[-1]['status'],'done')
        self.assertIn('z',panel.entries[-1]['answer']['expression'])
        self.assertEqual(window.project.headers()[-1]['parents'],[key])

    def test_marked_table_sample_can_navigate_to_figure_and_back(self):
        window=self.window()
        window.show()
        route=ROUTES['basic','generate']
        window.open_tool(route)
        page=window.pages[route]
        signal=Signal(np.arange(12)+1j*np.arange(12)*2,-5,name='Registro')
        key=window.publish(signal,operation='Muestras')
        view=page.basic_result
        view.show_result(signal)
        view.result_ids=[key]
        table=view.table_view
        table.set_signals((signal,))
        table.select_cell(8,2)
        table.update_plot_button()
        self.assertTrue(table.locate_plot.isEnabled())
        table.show_in_figure()
        canvas=view.canvas
        probe=canvas._signallab_probe
        self.assertTrue(probe.sample_points)
        self.assertEqual(probe.sample[2],8)
        self.assertEqual(probe.available_value_rows(table)[0][2],8)
        probe.open_values()
        self.assertEqual(table.model.offset+table.table.currentIndex().row(),8)
        self.assertIn('Desde el gráfico',table.coordinate_note.text())
        self.assertFalse(canvas._signallab_window.isVisible())

    def test_saved_record_views_preserve_typed_data_without_recalculation(self):
        from signallab_pc.state_space import StateModel
        window=self.window()
        values=[Signal([3,4j],-1,name='xs'),Transfer([1],[1,-.3],name='Filtro'),
                StateModel([[-2]],[[1]],[[3]],[[0]],name='Modelo'),
                {'report':'Magnitud física: 2 rad/s'}]
        ids=[window.publish(value, title=f'Registro {i}',operation='Evaluación original')
             for i,value in enumerate(values)]
        for key in ids:
            window.focus_result(key)
            window.open_selected_signal()
            self.assertEqual(window.stack.currentWidget(),window.pages[('saved_signal_view',key)])
            self.assertIn('conservado',window.stack.currentWidget().layout().itemAt(0).widget().text().lower())
            self.assertEqual(len(window.project.headers()),len(ids))
