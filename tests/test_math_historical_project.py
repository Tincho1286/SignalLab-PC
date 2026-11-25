"""Historical project reuse and independent references for scientific paths."""

from cmath import exp
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal
import sympy as sp

from signallab_pc import session
from signallab_pc.cas_engine import calculate
from signallab_pc.cas_import import import_result
from signallab_pc.cas_transfer import payload
from signallab_pc.filters import Transfer
from signallab_pc.project import Project
from signallab_pc.realization_graph import RealizationGraph
from signallab_pc.system_conditions import record

FIXTURES = Path(__file__).with_name('fixtures')


class HistoricalProjects(unittest.TestCase):
    def test_project_versions_reopen_with_clock_and_transitive_provenance(self):
        for schema, name in ((1,'project-v1-legacy-clock.json'),(2,'project-v2-roc-cas-2.0.0.json')):
            with self.subTest(schema=schema), TemporaryDirectory() as folder:
                project, workspace = session.load(FIXTURES/name)
                signal, system, second, last = project.headers()
                self.assertEqual(workspace, session.empty_workspace())
                self.assertEqual([system['parents'], second['parents'], last['parents']],
                                 [[signal['id']], [system['id']], [second['id']]])
                assert_array_equal(project.get(signal['id']).values,[1+2j,-3j,2])
                self.assertEqual(project.get(system['id']).sample_period_s,.125)
                self.assertEqual(project.get(system['id']).roc,{'mode':'left'} if schema==2 else None)
                path = Path(folder)/'saved.json'
                project.save(path)
                self.assertEqual(json.loads(path.read_text())['schema_version'],2)
                copy,_ = session.load(path)
                self.assertEqual(copy.headers(), project.headers())
                subset = Path(folder)/'subset.json'
                copy.export_record(last['id'], subset)
                imported = Project()
                self.assertEqual(imported.merge(subset),4)
                signal2, system2, second2, last2 = imported.headers()
                self.assertNotEqual(system2['id'],system['id'])
                self.assertEqual([system2['parents'], second2['parents'],last2['parents']],
                                 [[signal2['id']],[system2['id']],[second2['id']]])
                self.assertEqual(imported.get(system2['id']).sample_period_s,.125)
                self.assertEqual(imported.get(last2['id']),project.get(last['id']))

    def test_project_rejects_partial_merge_when_roc_or_lineage_is_invalid(self):
        source = json.loads((FIXTURES/'project-v2-roc-cas-2.0.0.json').read_text(encoding='utf-8'))
        missing = deepcopy(source); missing['records'][-1]['parents'] = ['unavailable']
        bad_roc = deepcopy(source); bad_roc['records'][1]['data']['roc'] = {'mode':'radius','radius':0}
        for document in (missing,bad_roc):
            with self.subTest(document=document['records'][1]['data']['roc']), TemporaryDirectory() as folder:
                project,_ = session.load(FIXTURES/'project-v2-roc-cas-2.0.0.json')
                before = project.document()
                path = Path(folder)/'invalid.json'
                path.write_text(json.dumps(document),encoding='utf-8')
                with self.assertRaises(ValueError):
                    project.merge(path)
                self.assertEqual(project.document(),before)

    def test_historical_cas_result_can_be_reused_in_a_new_worksheet(self):
        project,_ = session.load(FIXTURES/'project-v2-roc-cas-2.0.0.json')
        item = project.get(project.headers()[-1]['id'])
        restored = import_result({'cell':1, 'payload':payload(item)})
        expression = calculate({'cell':2,'source':'diff(r1,x)','state':restored['state']})
        self.assertEqual(sp.sympify(expression['expression']),12*sp.Symbol('x'))

    def test_graph_versions_preserve_transfer_signs_and_clock(self):
        for version in (1,2,3):
            with self.subTest(version=version):
                path = FIXTURES/f'diagram-v{version}-2.0.0.json'
                document = json.loads(path.read_text())
                self.assertEqual(document['version'],version)
                graph = RealizationGraph.from_document(document)
                self.assertEqual(graph.to_document(),document)
                expression = graph.transfer()
                omega = (0,.5,1.75)
                if version==1:
                    expected = [2,2,2]
                elif version==2:
                    expected = [1/(1-.5*exp(-1j*w)) for w in omega]
                else:
                    expected = [2/3]*3
                actual = [complex(expression.subs({symbol:exp(1j*w) for symbol in expression.free_symbols}))
                          for w in omega]
                assert_allclose(actual,expected,rtol=2e-14)
                self.assertEqual(graph.sample_period_s,.125 if version==2 else None)

    def test_outside_and_inside_rocs_have_different_physical_behavior(self):
        project,_ = session.load(FIXTURES/'project-v2-roc-cas-2.0.0.json')
        system = project.get(project.headers('system')[0]['id'])
        described = record(system)
        self.assertIn('excluye',described['bibo_stability'])
        with self.assertRaises(ValueError):
            system.excitation_response(6)
        causal = Transfer([1],[1,-.5],sample_period_s=.125,roc={'mode':'right'})
        assert_allclose(causal.excitation_response(6).values,[.5**n for n in range(6)])
        self.assertIn('pertenece',record(causal)['bibo_stability'])


class ScientificPaths(unittest.TestCase):
    def test_complex_frequency_response_includes_advance_and_analog_phase(self):
        omega = np.array([0,.25,1.5,2.9])
        a = Transfer([1,1],[1,2],domain='analog')
        z = Transfer([1,.25],[1,-.5],advance=2)
        assert_allclose(a.response(omega),[(1+1j*w)/(2+1j*w) for w in omega],rtol=3e-15)
        assert_allclose(z.response(omega),
                        [exp(2j*w)*(1+.25*exp(-1j*w))/(1-.5*exp(-1j*w))
                         for w in omega],rtol=3e-15)

    def test_incomplete_spectral_region_rejects_transform_and_isolated_hole_can_be_integrated(self):
        from signallab_pc.inverse_frequency_domain import require_inverse_domain
        from signallab_pc.symbolic import W

        domain = sp.Interval(-1,1)
        require_inverse_domain({'input_frequency_condition':'Ne(w,0)'},sp.S.One,domain,W)
        for condition, expression in (('w>0',sp.S.One),('Ne(w,0)',sp.DiracDelta(W))):
            with self.subTest(condition=condition), self.assertRaisesRegex(ValueError,'intervalo'):
                require_inverse_domain({'input_frequency_condition':condition},expression,domain,W)
