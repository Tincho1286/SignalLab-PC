"""Reopen scientific workspaces and contain bad drafts before switching projects."""
from copy import deepcopy
import json
from unittest.mock import patch

import numpy as np
from PySide6.QtWidgets import QMessageBox

from signallab_pc import session
from signallab_pc.model import Signal
from signallab_pc.result_expressions import send_expression
from signallab_pc.session_desktop import capture
from signallab_pc.tool_catalog import normalized_key
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


def tool_inputs(workspace, route):
    key = list(normalized_key(route))
    return next(tool['inputs'] for tool in workspace['tools'] if tool['route']==key)


class ScientificSessionDocuments(DesktopSessionFixture):
    def write_tool_document(self, window, label):
        path = self.path/(label+'.json')
        session.save(path,window.project,capture(window))
        return path,json.loads(path.read_text(encoding='utf-8'))

    def check_rejected(self, window, path, intact, route, changes):
        project = window.project
        old_records = project.headers()
        old_page = window.pages[route]
        for mutate, reason in changes:
            with self.subTest(reason=reason):
                bad = deepcopy(intact)
                mutate(tool_inputs(bad['workspace'],route))
                path.write_text(json.dumps(bad),encoding='utf-8')
                self.assertFalse(window.sessions.open_path(path))
                self.assertIn(reason,self.warning.call_args.args[-1])
                self.assertIs(window.project,project)
                self.assertEqual(project.headers(),old_records)
                self.assertIs(window.pages[route],old_page)

    def test_z_workspace_reopens_result_conditions_and_auxiliary_tabs(self):
        window = self.window()
        route = ROUTES['transform_lab','z']
        key = window.project.add({'result': {
            'result':'z/(z-1/2)','output_variable':'z','evaluated':True,
            'roc':'|z| > 1/2','roc_kind':'right','condition':'a>0',
        }})
        window.show_menu('Proyecto')
        send_expression(window,key,'inverse')
        panel = window.pages[route].panel
        panel.roc.setCurrentIndex(0)
        panel.start.setText('0')
        panel.count.setText('4')
        panel.include_samples.setChecked(True)
        panel.sample_scope.setCurrentIndex(0)
        window.show_menu('Biblioteca')
        path,intact = self.write_tool_document(window,'z-condicionada')
        inputs = tool_inputs(intact['workspace'],route)
        self.assertEqual(inputs['expression_context']['references']['_library_source'],key)
        self.assertIn('a>0',inputs['expression_context']['conditions'])
        self.check_rejected(window,path,intact,route,[
            (lambda data:data['expression_context'].update(conditions=[1]),'expresiones de texto'),
            (lambda data:data['expression_context'].update(references={'old_mode':key}),'referencias de la transformada'),
            (lambda data:data['expression_context']['references'].update(_library_source=7),'procedencia de la expresión'),
            (lambda data:data.update(source={}), 'entrada de la sesión no existe'),
        ])
        path.write_text(json.dumps(intact),encoding='utf-8')
        reopened = self.window()
        self.assertTrue(reopened.sessions.open_path(path))
        self.assertEqual(reopened.documents.tabData(reopened.documents.currentIndex()),
                         ('menu','Biblioteca'))
        self.assertIn(('menu','Proyecto'),[reopened.documents.tabData(i) for i in range(reopened.documents.count())])
        reopened.open_tool(route)
        panel = reopened.pages[route].panel
        self.assertEqual(panel._library_source[1],key)
        reopened.calculate_active()
        self.wait_for_calculation(reopened,timeout_ms=12000)
        self.assertEqual(panel.last['numeric_samples'],[[1.,0.],[.5,0.],[.25,0.],[.125,0.]])
        result_key = panel.records[panel.record_key()][2]
        record = next(row for row in reopened.project.headers() if row['id']==result_key)
        self.assertIn(key,record['parents'])

    def test_matrix_and_channel_errors_leave_the_current_model_available(self):
        window = self.window()
        route = ROUTES['state_space','simulation']
        window.open_tool(route)
        panel = window.pages[route].panel
        for label,text in {'A':'1/2','B':'2, 1','C':'3','D':'1, 0'}.items():
            panel.fields[label].setText(text)
        panel.domain.setCurrentIndex(1)
        panel.step.setText('1/8')
        panel.initial.setText('4')
        panel.decompose.setChecked(True)
        panel.inputs.field(0).set_source(Signal([1,2]),view=2)
        second_key = window.project.add(Signal([3,4]))
        panel.inputs.field(1).set_source(window.project.get(second_key),second_key,view=3)
        panel.inputs.channel.setCurrentIndex(1)
        path,intact = self.write_tool_document(window,'matrices-bancos')
        fields = tool_inputs(intact['workspace'],route)['fields']
        bank_name = next(iter(fields['inputs']['banks']))
        self.check_rejected(window,path,intact,route,[
            (lambda d:d['fields']['fields.A'].update(cells='0, 1'),'matriz inválida'),
            (lambda d:d['fields']['fields.A'].update(shape=[1,-1]),'dimensiones de la matriz'),
            (lambda d:d['fields']['fields.A'].update(cells=[[0,0]]),'celda de matriz inválida'),
            (lambda d:d['fields']['fields.A'].update(cells=[[0,0,'1'],[0,0,'2']]),'inválida o repetida'),
            (lambda d:d['fields']['inputs'].update(channel=7),'bancos de entradas inválidos'),
            (lambda d:d['fields']['inputs']['banks'].update({bank_name:{}}),'no contiene borradores'),
            (lambda d:d['fields']['inputs']['banks'].update({bank_name:[[0],[0]]}),'canal inválido o repetido'),
            (lambda d:d['fields'].update(do_not_restore=4),'campo incompatible'),
            (lambda d:d['fields'].update(decompose=1),'tipo o intervalo'),
        ])
        self.assertEqual(panel.fields['A'].text(),'1/2')
        path.write_text(json.dumps(intact),encoding='utf-8')
        reopened = self.window()
        self.assertTrue(reopened.sessions.open_path(path))
        panel = reopened.pages[route].panel
        self.assertTrue(panel.decompose.isChecked())
        self.assertEqual(panel.inputs.channel.currentIndex(),1)
        self.assertEqual(panel.inputs.field(1).loaded_reference_id,second_key)
        model = panel.read_model()
        samples = np.column_stack([source.values for source in panel.inputs.read()])
        time,y,_ = model.simulate(samples,initial=[4])
        np.testing.assert_array_equal(time,[0.,.125])
        np.testing.assert_array_equal(y[:,0],[13.,23.])

    def test_manual_save_as_binary_and_cancel_open_keep_the_same_workspace(self):
        from signallab_pc.session_desktop import _BINARY_SESSION
        window = self.window()
        route = ROUTES['basic','generate']
        window.open_tool(route)
        page = window.pages[route]
        page.first.expression.setText('n^2')
        recorded = window.project.add(Signal([3+2j,4],-7))
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName',return_value=('','')):
            window.sessions.open_dialog()
        self.assertEqual(window.current_operation,route)
        target = self.path/'borrador'
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName',
                   return_value=(str(target),_BINARY_SESSION)):
            self.assertTrue(window.sessions.save_dialog())
        binary = target.with_suffix('.slproj')
        self.assertTrue(binary.is_file())
        self.assertFalse(window.sessions.changed())
        original = window.project
        page.first.expression.setText('sin(n)')
        with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Cancel):
            self.assertFalse(window.sessions.open_path(binary))
        self.assertIs(window.project,original)
        self.assertEqual(page.first.expression.text(),'sin(n)')
        with patch('PySide6.QtWidgets.QFileDialog.getOpenFileName',return_value=(str(binary),'SLPROJ')):
            window.sessions.open_dialog()
        self.assertEqual(window.pages[route].first.expression.text(),'n^2')
        self.assertEqual(window.project.get(recorded).origin,-7)
        self.assertFalse(window.sessions.changed())

    def test_reloaded_expression_draft_links_original_result_and_new_samples(self):
        window = self.window()
        route = ROUTES['basic','generate']
        original = window.project.add({'result':{
            'result':'n^2 + 1','evaluated':True,'output_variable':'n','condition':'a>0',
        }})
        send_expression(window,original,'signal')
        field = window.pages[route].first
        field.origin.setText('-2')
        field.count.setText('4')
        path,intact = self.write_tool_document(window,'formula-muestras')
        inputs = tool_inputs(intact['workspace'],route)
        source_name = next(name for name,value in inputs['fields'].items()
                           if isinstance(value,dict) and value.get('expression',{}))
        self.assertEqual(inputs['fields'][source_name]['expression']['record'],original)
        self.check_rejected(window,path,intact,route,[
            (lambda data:data['fields'][source_name].update(sources={'3':[]}), 'referencia de entrada inválida'),
            (lambda data:data['fields'][source_name].update(view=True), 'selector de entrada inválido'),
            (lambda data:data['fields'][source_name]['expression'].update(conditions=[8]),'condiciones de la expresión'),
        ])
        path.write_text(json.dumps(intact),encoding='utf-8')
        reopened = self.window()
        self.assertTrue(reopened.sessions.open_path(path))
        page = reopened.pages[route]
        self.assertEqual(page.first._expression_origin[1],original)
        reopened.calculate_active()
        self.wait_for_calculation(reopened)
        output = page.basic_result.result
        np.testing.assert_array_equal(output.axis,[-2,-1,0,1])
        np.testing.assert_array_equal(output.values,[5,2,1,2])
        records = {row['id']:row for row in reopened.project.headers()}
        self.assertEqual(records[page.first.reference_id]['parents'],[original])
        self.assertEqual(records[page.basic_result.result_ids[0]]['parents'],[page.first.reference_id])
