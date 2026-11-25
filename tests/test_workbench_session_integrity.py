"""Preflight checks for structured drafts and real restoration of expression links."""
from copy import deepcopy
import json

import numpy as np

from signallab_pc import session
from signallab_pc.model import Signal
from signallab_pc.result_expressions import ExpressionResult
from signallab_pc.session_desktop import capture
from signallab_pc.workspaces import ROUTES
from test_desktop_session import DesktopSessionFixture


class SessionDraftContracts(DesktopSessionFixture):
    def test_compact_session_reopens_formula_conditions_and_invalidation_follows_edits(self):
        window=self.window()
        origin=window.project.add({'result':{'result':'1/2','evaluated':True,'output_variable':'w',
                                              'frequency_condition':'Ne(w,0)'}})
        route=ROUTES['dtft_symbolic',1]
        window.open_tool(route)
        panel=window.pages[route].panel
        expression=ExpressionResult('1/2','w',conditions=('a>0',),units='rad/muestra')
        panel.load_expression(expression,origin)
        state=capture(window)
        path=self.path/'linked.slproj'
        session.save(path,window.project,state)
        reopened=self.window()
        self.assertTrue(reopened.sessions.open_path(path))
        panel=reopened.pages[route].panel
        self.assertEqual(panel._expression_origin[1],origin)
        self.assertEqual(panel._input_conditions,('a>0',))
        self.assertEqual(panel._frequency_condition,'Ne(w,0)')
        panel.expression.setText('2')
        captured=capture(reopened)['tools'][0]['inputs']
        self.assertNotIn('expression_context',captured)

    def test_invalid_editor_tables_preserve_preexisting_session_and_can_be_reopened(self):
        window=self.window()
        route=ROUTES['signal_editor',0]
        window.open_tool(route)
        panel=window.pages[route].panel
        initial=Signal([1,3,8],-2,name='Reloj de prueba',metadata={'sample_rate_hz':8,'time_start_s':.25})
        parent=window.project.add(initial)
        panel.receive(initial,parent)
        panel.history.values([1],[5-7j])
        path=self.path/'draft.json'
        session.save(path,window.project,capture(window))
        intact=json.loads(path.read_text(encoding='utf-8'))
        variants=[
            ({'offset':3},'página válida'),
            ({'offset':1},'página válida'),
            ({'pending':'yes'},'no corresponde'),
            ({'pending':False},'ediciones de muestras inválidas'),
            ({'edits':[[1,3,0],[1,3,0]]},'fila editada inválida'),
            ({'edits':[[1,5,-7]]},'no difiere'),
            ({'edits':[[1,'3',0]]},'fila editada inválida'),
            ({'signal':{'record':0}},'tipo esperado'),
            ({'signal':{'type':'arbitrary'}},'tipo de entrada'),
        ]
        project=window.project
        for change,reason in variants:
            with self.subTest(change=change):
                corrupted=deepcopy(intact)
                corrupted['workspace']['tools'][0]['inputs']['table'].update(change)
                path.write_text(json.dumps(corrupted),encoding='utf-8')
                self.assertFalse(window.sessions.open_path(path))
                self.assertIn(reason,self.warning.call_args.args[-1])
                self.assertIs(window.project,project)
                self.assertEqual(len(project.headers()),1)
                self.assertIs(window.pages[route].panel,panel)
                self.assertEqual(panel.staged_signal().values[1],5-7j)
        path.write_text(json.dumps(intact),encoding='utf-8')
        self.assertTrue(window.sessions.open_path(path))
        saved=window.pages[route].panel
        self.assertEqual(saved.parent_id,parent)
        self.assertEqual(saved.staged_signal().metadata['time_start_s'],.25)
        np.testing.assert_array_equal(saved.staged_signal().values,[1,5-7j,8])
