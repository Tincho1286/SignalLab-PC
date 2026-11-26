"""Import, design and inspect filters through their actual workbench tools."""
import csv
import json
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from PySide6.QtWidgets import QFileDialog

from signallab_pc.filters import Transfer
from signallab_pc.project import Project
from signallab_pc.symbolic import execute
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class SystemSurfaceContracts(DesktopSessionFixture):
    def analysis(self):
        window = self.window()
        route = ROUTES['system_analysis',0]
        window.open_tool(route)
        return window,window.pages[route].panel

    def test_figure_launcher_keeps_calculated_views_after_switching_workspace_layout(self):
        from PySide6.QtTest import QTest

        window = self.window()
        window.resize(800,600)
        window.show()
        route = ROUTES['system_analysis',0]
        window.open_tool(route)
        page = window.pages[route]
        panel = page.panel
        panel.count.setText('31')
        self.app.processEvents()
        self.assertTrue(page.workspace.compact)
        window.calculate_active()
        self.wait_for_calculation(window,12000)
        measurement = panel.measurements
        panel.result_tabs.setCurrentIndex(panel.measurements_index)
        measurement.points.setText('1')
        measurement.calculate_button.click()
        self.wait_for_calculation(window,12000)
        reading, = measurement.result['rows']
        self.assertAlmostEqual(reading['magnitude'],1/np.sqrt(2))
        self.assertAlmostEqual(reading['delay'],0.5)

        launcher = page.workspace.results.graph_launcher
        for width,compact in ((800,True),(1200,False),(800,True)):
            with self.subTest(width=width):
                window.resize(width,600)
                QTest.qWait(30)
                self.assertEqual(page.workspace.compact,compact)
                self.assertTrue(launcher.isEnabled())
                entries = {entry[0]():entry for entry in launcher.available()}
                self.assertIn(panel.canvas,entries)
                self.assertIn(measurement.canvas,entries)
                launcher.open_entry(entries[measurement.canvas])
                self.assertTrue(measurement.canvas._signallab_window.isVisible())
                measurement.canvas._signallab_window.hide()

    def test_project_import_selects_the_last_system_and_rejects_unrelated_records(self):
        window,panel = self.analysis()
        panel.count.setText('21')
        unrelated = Project()
        unrelated.add({'report':'Apuntes de muestreo'})
        path = self.path/'sin-sistema.json'
        unrelated.save(path)
        panel.system_import.open_file(path)
        self.assertIn('no contiene una definición',self.warning.call_args.args[-1])
        self.assertEqual(window.project.headers(),[])

        request = dict(operation='system_formula',expression='z/(z-1/2)',domain='digital')
        result = execute(request)
        request['roc_spec'] = {'mode':'right'}
        result['sample_period_s'] = .125
        external = Project()
        external.add(Transfer([3],[1,1],'analog','Sistema anterior'))
        origin = external.add({'report':'Notas de la identificación'})
        external.add(dict(request=request,result=result),parents=[origin])
        external.add({'report':'Comentario más reciente'})
        path = self.path/'sistemas.json'
        external.save(path)
        with patch.object(QFileDialog,'getOpenFileName',return_value=(str(path),'JSON')):
            panel.system_import.open_file()
        self.assertEqual(panel.definition_mode.currentIndex(),1)
        self.assertEqual(panel.domain.currentIndex(),1)
        definitions = window.project.headers()
        self.assertEqual(definitions[-1]['operation'],'Importación de definición de sistema')
        stored_key = definitions[-1]['id']
        selected = window.project.get(stored_key)
        self.assertEqual(selected['request']['expression'],request['expression'])
        window.calculate_active()
        self.wait_for_calculation(window,timeout_ms=12000)
        frequency = panel.frequency_data
        self.assertIsNotNone(frequency)
        z = np.exp(1j*frequency.omega)
        np.testing.assert_allclose(frequency.response,z/(z-.5),atol=1e-13)
        self.assertEqual(panel.system.sample_period_s,.125)
        self.assertEqual(panel.system.roc,{'mode':'right'})
        self.assertEqual(window.project.describe(stored_key)['kind'],'calculation')

    def test_zero_transfer_explains_undefined_phase_then_draws_and_exports_margins(self):
        window,panel = self.analysis()
        panel.b.setText('0')
        panel.a.setText('1')
        panel.count.setText('13')
        window.calculate_active()
        self.wait_for_calculation(window,timeout_ms=12000)
        response = panel.frequency_data
        self.assertTrue(np.all(response.response==0))
        self.assertFalse(np.isfinite(response.phase).any())
        panel.magnitude_scale.setCurrentIndex(1)
        self.assertIn('Módulo cero',panel.figure.axes[0].texts[0].get_text())
        self.assertIn('Ángulo no definido',panel.figure.axes[1].texts[0].get_text())

        panel.margins.setChecked(True)
        panel.frequency_scale.setCurrentIndex(1)
        panel.w0.setText('1/10')
        panel.w1.setText('8')
        panel.count.setText('81')
        panel.b.setText('16')
        panel.a.setText('1, 3, 3, 1')
        window.calculate_active()
        self.wait_for_calculation(window,timeout_ms=12000)
        response = panel.frequency_data
        expected_gain = np.sqrt(16**(2/3)-1)
        expected_phase = np.sqrt(3)
        gain, = response.margins['gain_crossings']
        phase, = response.margins['phase_crossings']
        self.assertAlmostEqual(gain['frequency'],expected_gain,places=6)
        self.assertAlmostEqual(phase['frequency'],expected_phase,places=6)
        self.assertEqual(panel.figure.axes[0].get_xscale(),'log')
        self.assertIn('Cruce de ganancia',panel.figure.axes[0].get_legend_handles_labels()[1])
        panel.response_components.setCurrentIndex(1)
        np.testing.assert_allclose(panel.figure.axes[1].lines[0].get_ydata(),
                                   (16/(1+1j*response.omega)**3).imag,atol=1e-13)
        target = self.path/'margenes'
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(target),'Tabla CSV')):
            panel.export_response()
        with target.with_suffix('.csv').open(newline='',encoding='utf-8-sig') as stream:
            rows = list(csv.reader(line for line in stream if not line.startswith('#')))
        self.assertEqual(len(rows),1+len(response.omega))
        self.assertTrue(all(np.isfinite(float(row[0])) for row in rows[1:]))

    def test_existing_roots_open_without_frequency_data_and_are_cached(self):
        window,panel = self.analysis()
        system = Transfer([1,0],[1,-.5],name='Filtro con retardo')
        key = window.publish(system)
        window.open_root_analysis(system,key)
        self.wait_for_calculation(window,timeout_ms=12000)
        self.assertIsNone(panel.frequency_data)
        self.assertIs(panel.result_tabs.currentWidget(),panel.roots_view)
        self.assertFalse(panel.frequency_export.isEnabled())
        self.assertIs(panel.system,system)
        cached = panel._roots_cache
        self.assertIs(cached[0],system)
        before = window.project.headers()
        panel.show_poles_zeros()
        self.assertIs(panel._roots_cache[2],cached[2])
        self.assertEqual(window.project.headers(),before)

    def test_phase_tool_rejects_analog_sources_and_keeps_a_digital_expression_exact(self):
        from signallab_pc.transfer_input import read_system

        window = self.window()
        route = ROUTES['course_tools','phase']
        window.open_tool(route)
        panel = window.pages[route].panel
        analog_transfer = Transfer([1],[1,2],'analog','Filtro analógico')
        wrong = self.path/'analogico.json'
        wrong.write_text(json.dumps(analog_transfer.to_document()),encoding='utf-8')
        panel.system_import.open_file(wrong)
        self.assertIn('dominio no corresponde',self.warning.call_args.args[-1])
        self.assertEqual(window.project.headers(),[])
        request = dict(operation='system_formula',expression='1/(s+2)',domain='analog')
        analog = window.publish(dict(request=request,result=execute(request)))
        panel.system_import.load_result(analog)
        self.assertIn('otro dominio',self.warning.call_args.args[-1])
        self.assertEqual(len(window.project.headers()),1)

        request = dict(operation='system_formula',expression='(z+2)/(z-1/2)',domain='digital')
        result = execute(request)
        result['sample_period_s']=.25
        request['roc_spec']={'mode':'right'}
        key = window.publish(dict(request=request,result=result))
        panel.system_import.load_result(key)
        self.wait_for_calculation(window,timeout_ms=12000)
        self.assertEqual(panel.definition_mode.currentIndex(),1)
        self.assertEqual(panel.transfer_formula.text(),result['transfer'])
        system = read_system(panel)
        self.assertEqual(system.sample_period_s,.25)
        self.assertEqual(system.roc,{'mode':'right'})
        self.assertEqual(window.project.headers()[-1]['parents'],[key])
        z = np.exp(1j*np.array([0,.4,1.2]))
        np.testing.assert_allclose(system.response([0,.4,1.2]),(z+2)/(z-.5),atol=1e-13)

    def test_polar_editor_adds_a_negative_zero_and_removes_a_conjugate_pair(self):
        window = self.window()
        route = ROUTES['systems',6]
        window.open_tool(route)
        page = window.pages[route]
        panel,editor = page.panel,page.pole_editor
        panel.fields['zeros'].clear()
        panel.fields['poles'].setText('i/2, -i/2')
        editor.pairs.setChecked(True)
        editor.coordinates.setCurrentIndex(1)
        editor.manual()
        axis = panel.figure.axes[0]
        before = axis.get_ylim()[1]
        editor.zoom(2)
        self.assertAlmostEqual(axis.get_ylim()[1],2*before)

        def event(x,y,name='button_press_event'):
            axis = panel.figure.axes[0]
            px,py = axis.transData.transform((x,y))
            return SimpleNamespace(button=1,inaxes=axis,xdata=x,ydata=y,x=px,y=py,name=name)

        editor.mode.setCurrentIndex(1)
        editor.cursor_event(event(np.pi,2,'axes_enter_event'))
        self.assertIn('agregar un cero',editor.note.text())
        editor.press(event(np.pi,2))
        self.wait_for_calculation(window,timeout_ms=12000)
        self.assertEqual(editor.data()[0],[-2])
        self.assertEqual(editor.data()[1],[.5j,-.5j])
        editor.mode.setCurrentIndex(3)
        editor.press(event(np.pi/2,.5))
        self.wait_for_calculation(window,timeout_ms=12000)
        self.assertEqual(editor.data(),[[-2],[]])
        key = window.project.headers('system')[-1]['id']
        system = window.project.get(key)
        omega = np.array([0.,.3,1.])
        np.testing.assert_allclose(system.response(omega),np.exp(1j*omega)+2,atol=1e-13)
        editor.cursor_event(SimpleNamespace(name='axes_leave_event',inaxes=None))
        self.assertFalse(editor._inside)
