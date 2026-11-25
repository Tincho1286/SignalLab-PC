from copy import deepcopy
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from textwrap import dedent
import unittest
from unittest.mock import patch

from signallab_pc.cas_worksheet import prepare
from signallab_pc.project import Project


class CasSessionContractTests(unittest.TestCase):
    def make_sheet(self):
        project = Project()
        source = 'a := 2+3*i'
        value = 'Add(Integer(2), Mul(Integer(3), I))'
        record = project.add({'source': source, 'cas_answer': {
            'encoded_value': value, 'text': '2 + 3*i', 'notices': [], 'symbols': []}})
        state = dict(version=1, variables={'a': value}, functions={'f': {
            'parameters': ['t'], 'body': "Symbol('t')"}}, results={'1': value},
            ans=1, assumptions={'x': {'flags': {'positive': True}}})
        sheet = dict(version=1, state=state, entries=[
            dict(cell=1, source=source, imported=False, status='done', result_id=record),
            dict(cell=2, source='a :=', imported=False, status='error', error='Expresión incompleta')],
            input='factor(', commands=[source, 'a :='], draft='', command_position=2,
            selected=1, math_size=17, digits='24', bindings=[['a', '2+3*i']])
        return sheet, project

    def test_detached_sheet_preserves_error_and_draft_without_symbolic_deserialization(self):
        sheet, project = self.make_sheet()
        with patch('signallab_pc.cas_engine.restore', side_effect=AssertionError('Unexpected symbolic load')):
            hydrated = prepare(sheet, project)
        self.assertEqual(hydrated['entries'][0]['answer']['text'], '2 + 3*i')
        self.assertEqual(hydrated['entries'][1], sheet['entries'][1])
        self.assertEqual(hydrated['input'], 'factor(')
        hydrated['state']['variables'].clear()
        self.assertIn('a', sheet['state']['variables'])
        self.assertEqual(len(project.headers()), 1)

    def test_incomplete_or_inconsistent_sheets_are_rejected_before_attachment(self):
        sheet, project = self.make_sheet()
        state = sheet['state']
        invalid = [
            ({**sheet, 'version': 2}, 'Versión de hoja'),
            ({**sheet, 'state': {**state, 'version': True}}, 'Versión de estado'),
            ({**sheet, 'state': {**state, 'assumptions': []}}, 'definiciones'),
            ({**sheet, 'state': {**state, 'variables': {'a': None}}}, 'valor simbólico'),
            ({**sheet, 'state': {**state, 'functions': {'f': {'parameters': [], 'body': 42}}}}, 'función'),
            ({**sheet, 'state': {**state, 'result_contexts': {'1': 'x>0'}}}, 'condiciones'),
            ({**sheet, 'input': {}}, 'entrada'),
            ({**sheet, 'bindings': ['a']}, 'configuración'),
            ({**sheet, 'entries': [sheet['entries'][0]]*2}, 'repetidas'),
            ({**sheet, 'entries': [sheet['entries'][0], {**sheet['entries'][1], 'status': 'pending'}]}, 'incompleta'),
            ({**sheet, 'entries': sheet['entries'][1:]}, 'resultados exactos'),
            ({**sheet, 'selected': 2}, 'sin resultado'),
        ]
        altered = deepcopy(sheet)
        altered['state']['results']['1'] = 'Integer(1)'
        invalid.append((altered, 'resultado publicado'))
        for document, message in invalid:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    prepare(document, project)
        self.assertEqual(len(project.headers()), 1)

    def test_headless_archive_reads_cas_contract_without_qt_or_symbolic_evaluation(self):
        from signallab_pc import session

        worksheet, project = self.make_sheet()
        with TemporaryDirectory() as folder:
            path = Path(folder)/'headless.slproj'
            session.save(path, project, {**session.empty_workspace(), 'cas': worksheet})
            script = dedent('''
                import importlib.abc
                import sys

                class NoGuiOrCasEngine(importlib.abc.MetaPathFinder):
                    def find_spec(self, name, path=None, target=None):
                        if name.startswith(('PySide6', 'shiboken6', 'signallab_pc.cas_engine')):
                            raise AssertionError(name)

                sys.meta_path.insert(0, NoGuiOrCasEngine())
                from signallab_pc import session
                from signallab_pc.cas_worksheet import prepare

                project, workspace = session.load(sys.argv[1])
                sheet = prepare(workspace['cas'], project)
                assert sheet['input'] == 'factor('
                assert sheet['entries'][0]['answer']['text'] == '2 + 3*i'
            ''')
            child = subprocess.run([sys.executable,'-B','-c',script,str(path)],
                                   check=False, text=True, capture_output=True, timeout=30)
            self.assertEqual(child.returncode, 0, child.stderr)
