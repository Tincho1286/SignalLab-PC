"""Exercise tabular imports with real files, units and project handoffs."""
from unittest.mock import patch

import numpy as np
from PySide6.QtWidgets import QDialog, QFileDialog, QInputDialog
from scipy.io import savemat

from signallab_pc.csv_import_dialog import CsvImportDialog
from signallab_pc.matlab_import_dialog import MatlabImportDialog
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.project_picker import ProjectPicker
from signallab_pc.storage import save_csv, save_json
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class SignalImportContracts(DesktopSessionFixture):
    def test_matlab_menu_cancellation_and_retry_publish_only_the_accepted_channel(self):
        window = self.window()
        path = self.path/'sesion.m'
        path.write_text('t = 0:0.25:0.5; A = [t; 1 + 2*t].\';\n',encoding='utf-8')
        with patch.object(QFileDialog,'getOpenFileName',return_value=('','')):
            window.import_matlab()
        self.assertEqual(window.project.headers(),[])
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'')), \
             patch.object(MatlabImportDialog,'exec',return_value=QDialog.DialogCode.Rejected):
            window.import_matlab()
        self.assertEqual(window.project.headers(),[])

        def select(dialog):
            dialog.domain.setCurrentIndex(dialog.domain.findData('continuous'))
            dialog.variable.setCurrentIndex(dialog.variable.findData('A'))
            dialog.axis.setCurrentIndex(dialog.axis.findData('t'))
            dialog.column.setValue(2)
            dialog.load()
            return dialog.result()

        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'')), \
             patch.object(MatlabImportDialog,'exec',select):
            window.import_matlab()
        record, = window.project.headers()
        result = window.project.get(record['id'])
        np.testing.assert_array_equal(result.axis,[0,0.25,0.5])
        np.testing.assert_array_equal(result.values,[1,1.5,2])
        self.assertIn('disponible para reutilizar',window.statusBar().currentMessage())

    def test_external_file_and_project_result_keep_independent_drafts_and_survive_clear(self):
        window = self.window()
        route = ROUTES['basic','generate']
        window.open_tool(route)
        field = window.pages[route].first
        project_value = Signal([8,12],origin=3,name='Resultado guardado')
        project_key = window.publish(project_value,operation='Otra herramienta')
        field.set_source(project_value,project_key)
        path = self.path/'entrada.json'
        save_json(Signal([1,2j],origin=-2,name='Datos del laboratorio'),path)
        field.entry_modes.select(2)
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'')):
            field.open_file()
        self.assertEqual(field.loaded.origin,-2)
        field.entry_modes.select(3)
        self.assertEqual(field.loaded_reference_id,project_key)
        field.entry_modes.select(2)
        self.assertEqual(field.loaded.name,'Datos del laboratorio')
        field.clear_source()
        self.assertIsNone(field.loaded)
        self.assertIsNone(field.loaded_reference_id)
        field.entry_modes.select(3)
        self.assertEqual(field.loaded_reference_id,project_key)
        window.calculate_active()
        self.wait_for_calculation(window)
        self.assertEqual(window.project.headers()[-1]['parents'],[project_key])

    def test_csv_table_uses_coordinates_instead_of_unused_grid_fields(self):
        path = self.path/'laboratorio.csv'
        path.write_text('t;real;imag\n0,1;2,0;-1,0\n0,3;4,0;0,5\n0,5;6,0;2,0\n',encoding='utf-8')
        dialog = CsvImportDialog(path,'continuous',self.window())
        self.assertEqual(dialog.delimiter.currentData(),';')
        self.assertFalse(dialog.domain.isEnabled())
        dialog.units.setCurrentIndex(dialog.units.findData('ms'))
        dialog.decimal.setChecked(True)
        dialog.imag.setValue(3)
        dialog.origin.clear()
        dialog.step.clear()
        dialog.load()
        self.warning.assert_not_called()
        signal = dialog.result_signal
        np.testing.assert_allclose(signal.axis, [0.0001,0.0003,0.0005],rtol=1e-14)
        np.testing.assert_array_equal(signal.values,[2-1j,4+0.5j,6+2j])
        self.assertEqual((signal.units,signal.metadata['source_axis_units']),('s','ms'))

    def test_single_row_with_explicit_axis_requires_only_a_step_in_continuous_domain(self):
        path = self.path/'detector.tsv'
        path.write_text('W\tA\n3\t12\n',encoding='utf-8')
        dialog = CsvImportDialog(path,'import',self.window())
        dialog.domain.setCurrentIndex(dialog.domain.findData('frequency'))
        dialog.units.setCurrentIndex(dialog.units.findData('rad/muestra'))
        dialog.origin.setText('origin unused')
        dialog.step.setText('0')
        dialog.load()
        self.assertIsNone(dialog.result_signal)
        self.assertIn('paso debe ser positivo',self.warning.call_args.args[-1])
        dialog.step.setText('0.25')
        dialog.load()
        self.assertEqual(dialog.result(),QDialog.DialogCode.Accepted)
        self.assertEqual((dialog.result_signal.origin,dialog.result_signal.step,dialog.result_signal.units),
                         (3,0.25,'rad/muestra'))

    def test_matlab_channel_retries_a_bad_axis_without_losing_the_selected_column(self):
        path = self.path/'receptor.mat'
        samples = np.array([[1,2+3j],[5,7-1j],[9,11]])
        savemat(path,{'channels':samples,'bad_axis':[0,1.5,2],'n':[-2,-1,0]},do_compression=True)
        dialog = MatlabImportDialog(path,'discrete',self.window())
        dialog.variable.setCurrentIndex(dialog.variable.findData('channels'))
        dialog.column.setValue(2)
        dialog.axis.setCurrentIndex(dialog.axis.findData('bad_axis'))
        dialog.load()
        self.assertIsNone(dialog.result_signal)
        self.assertIn('consecutivos',self.warning.call_args.args[-1])
        dialog.axis.setCurrentIndex(dialog.axis.findData('n'))
        dialog.origin.clear()
        dialog.step.clear()
        dialog.load()
        self.assertEqual(dialog.result(),QDialog.DialogCode.Accepted)
        np.testing.assert_array_equal(dialog.result_signal.axis,[-2,-1,0])
        np.testing.assert_array_equal(dialog.result_signal.values,samples[:,1])
        self.assertEqual(dialog.result_signal.metadata['column'],2)
        self.assertEqual(dialog.result_signal.metadata['axis_variable'],'n')

    def test_picker_imports_own_csv_and_filters_without_changing_its_domain(self):
        window = self.window()
        path = self.path/'medición.csv'
        expected = Signal([2-3j,0],origin=0.5,step=0.125,units='s',domain='continuous',name='Medición RC')
        save_csv(expected,path)
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'')):
            incompatible = ProjectPicker(window,'signal',domains=['discrete'])
            incompatible.import_button.click()
            self.assertIsNone(incompatible.selected_id)
            self.assertEqual(window.project.headers(),[])
            self.assertIn('no contiene datos compatibles',self.warning.call_args.args[-1])
            picker = ProjectPicker(window,'signal',domains=['continuous'])
            picker.import_button.click()
        self.assertEqual(picker.result(),QDialog.DialogCode.Accepted)
        selected = window.project.get(picker.selected_id)
        np.testing.assert_array_equal(selected.values,expected.values)
        np.testing.assert_array_equal(selected.axis,expected.axis)
        record = window.project.headers()[0]
        self.assertIn(path.name,record['operation'])
        picker = ProjectPicker(window,'signal',domains=['continuous'])
        picker.search.setText('medicion rc')
        self.assertEqual(picker.selected_id,record['id'])
        picker.search.setText('aliasing')
        self.assertFalse(picker.use.isEnabled())
        self.assertIsNone(picker.selected_id)

    def test_picker_cancellation_in_a_multirecord_archive_does_not_publish_ancestors(self):
        window = self.window()
        source = Project()
        root = source.add(Signal([1],name='Origen'),operation='Medir')
        source.add(Signal([3],name='Amplificada'),operation='Ganancia',parents=[root])
        path = self.path/'comparacion.json'
        source.save(path)
        picker = ProjectPicker(window,'signal',domains=['discrete'])
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'')), \
             patch.object(QInputDialog,'getItem',return_value=('',False)) as confirm:
            picker.import_button.click()
            self.assertEqual(window.project.headers(),[])
            self.assertIsNone(picker.selected_id)
            labels = confirm.call_args.args[3]
            self.assertEqual(len(labels),2)
            confirm.return_value = (labels[1],True)
            picker.import_button.click()
        headers = window.project.headers()
        self.assertEqual(headers[-1]['id'],picker.selected_id)
        self.assertEqual(headers[-1]['parents'],[headers[0]['id']])
        self.assertTrue(headers[-1]['operation'].endswith('Ganancia'))
