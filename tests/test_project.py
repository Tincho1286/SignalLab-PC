import json
import tempfile
import unittest
from pathlib import Path
from signallab_pc.project import Project
from signallab_pc.model import Signal
from signallab_pc.filters import Transfer

class ProjectTests(unittest.TestCase):
    def test_snapshots_and_provenance(self):
        p=Project();source=Signal([1,2j],-2);a=p.add(source);source.values[0]=99
        self.assertEqual(p.get(a).values[0],1)
        copy=p.get(a);copy.values[0]=55;self.assertEqual(p.get(a).values[0],1)
        b=p.add(Transfer([1],[1,-.5]),parents=[a],operation='diseño')
        self.assertEqual(p.records()[1]['parents'],[a])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'project.json';p.save(path);q=Project();q.merge(path)
            self.assertEqual(len(q.records()),2)
            self.assertEqual(q.records()[1]['parents'],[q.records()[0]['id']])
            self.assertEqual(q.get(q.records()[1]['id']).domain,'digital')
            q.merge(path);self.assertEqual(len(q.records()),4)
            self.assertEqual(q.records()[3]['parents'],[q.records()[2]['id']])
    def test_invalid_import_is_atomic(self):
        p=Project();p.add(Signal([1]));original=p.records()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.json';p.save(path)
            doc=json.loads(path.read_text());doc['records'][0]['parents']=['missing'];path.write_text(json.dumps(doc))
            with self.assertRaises(ValueError):p.merge(path)
        self.assertEqual(p.records(),original)
    def test_symbolic_payload(self):
        p=Project();key=p.add({'expression':'1/(s+1)','result':'exp(-t)','assumptions':['t >= 0']},title='Laplace')
        self.assertEqual(p.get(key)['result'],'exp(-t)')

if __name__=='__main__':unittest.main()
