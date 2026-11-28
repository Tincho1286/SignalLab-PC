from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest

import numpy as np
from numpy.testing import assert_allclose, assert_array_equal

from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.project_archive import MAGIC, MAGIC_RF
from signallab_pc.resources import ResourceLimitError
from signallab_pc.rf_network import RFNetwork, renormalize
from signallab_pc.rf_storage import decode_network, encode_network, load_network, store_network
from signallab_pc.session import empty_workspace, load, save
from signallab_pc.touchstone import read_touchstone, write_touchstone


class TouchstoneTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)

    def create(self, name, content):
        path=self.folder/name
        path.write_bytes(content.encode('ascii'))
        return path

    def test_v1_documented_port_order_units_and_random_option_order(self):
        path=self.create('nonreciprocal.s2p', '! labels\r\n# RI R 75 mHz S\r\n1 .1 .3 .7 .2 .002 .004 -.2 .2 ! row\r\n')
        net=read_touchstone(path)
        assert_array_equal(net.frequencies_hz, [1e6])
        assert_allclose(net.values[0], [[.1+.3j,.002+.004j],[.7+.2j,-.2+.2j]])
        assert_array_equal(net.reference_ohm, [[75,75]])
        self.assertEqual(net.metadata['source_sha256'],sha256(path.read_bytes()).hexdigest())
        self.assertEqual(net.metadata['source_file'],'nonreciprocal.s2p')
        default = read_touchstone(self.create('open.s1p', '#\n1 1 0\n'))
        assert_array_equal(default.frequencies_hz,[1e9])
        assert_array_equal(default.values.real,1)
        assert_array_equal(default.reference_ohm,50)

    def test_real_physical_units_for_y_z_in_both_versions(self):
        variants=(
            ('y.s1p','# kHz Y RI R 75\n2 1 -.75\n','Y',(1-.75j)/75),
            ('z.s1p','# kHz Z MA R 75\n2 1 270\n','Z',-75j),
            ('physical.ts','[Version] 2.0\n# kHz Z MA R 75\n[Number of Ports] 1\n'
             '[Number of Frequencies] 1\n[Network Data]\n2 1 -90\n[End]\n','Z',-1j),
            ('attenuator.s1p','# kHz S DB\n2 -20 45\n','S',.1*np.exp(1j*np.pi/4)),
        )
        for name, content, parameters, expected in variants:
            with self.subTest(name=name):
                net = read_touchstone(self.create(name, content))
                self.assertEqual(net.representation,parameters)
                assert_allclose(net.values[0,0,0],expected,atol=3e-14)
                assert_array_equal(net.frequencies_hz,[2000])

    def test_v2_unequal_references_and_triangular_matrix(self):
        prefix='[Version] 2.0\n# Hz S RI R 50\n[Number of Ports] 3\n[Number of Frequencies] 1\n'
        for shape, row in (('Lower','3 11 1\n12 2 22 3\n13 4 23 5 33 6'),
                           ('Upper','3 11 1 12 2 13 4\n22 3 23 5\n33 6')):
            path=self.create('three.ts',prefix+'[Reference] 50 75\n100\n'
                               f'[Matrix Format] {shape}\n[Network Data]\n{row}\n[End]\n')
            net=read_touchstone(path)
            assert_array_equal(net.reference_ohm,[[50,75,100]])
            assert_array_equal(net.values[0],[[11+1j,12+2j,13+4j],[12+2j,22+3j,23+5j],[13+4j,23+5j,33+6j]])
        np.testing.assert_array_equal(net.frequencies_hz,[3])

    def test_export_preserves_nonreciprocal_matrices_and_port_references(self):
        f=[0,5,100]
        net=RFNetwork(f,np.arange(12).reshape(3,2,2)*(1+.1j),reference_ohm=[50,100])
        for version in ('1.0','2.0'):
            with self.subTest(version=version):
                file=self.folder/('test.s2p' if version=='1.0' else 'test.ts')
                source=renormalize(net,50) if version=='1.0' else net
                write_touchstone(file,source,version=version)
                reopened=read_touchstone(file)
                assert_array_equal(reopened.frequencies_hz,f)
                assert_array_equal(reopened.reference_ohm,source.reference_ohm)
                assert_array_equal(reopened.values,source.values)
        for representation in ('Y','Z'):
            rows=np.arange(27).reshape(3,3,3)*(.5-2j)
            source=RFNetwork(f,rows,representation=representation)
            file=self.folder/'test.s3p'
            write_touchstone(file,source,version='1.0')
            assert_allclose(read_touchstone(file).values,rows,atol=1e-14)

    def test_structural_limits_and_ambiguous_data_rejected(self):
        v2='[Version] 2.0\n# Hz RI\n[Number of Ports] 2\n[Number of Frequencies] 1\n'
        options=[
            ('many.s999p','#\n1 1 0'),
            ('empty.s1p',''),
            ('bad.s1p','# Hz S RI R 50 R 75\n1 0 0'),
            ('bad.s1p','# Hz S RI\n1 inf 0'),
            ('bad.s1p','# Hz S MA\n1 -1 0'),
            ('bad.s1p','# Hz S RI\n1 0 0\n1 0 0'),
            ('bad.s1p','# Hz S RI\n-1 0 0'),
            ('bad.s2p','# Hz S RI\n1 0 0 1 0 1 0 0 0\n.8 2 0 0 .5'),
            ('bad.ts','[Version] 2.1\n#\n'),
            ('bad.ts','#\n1 0 0'),
            ('bad.ts',v2+'[Network Data]\n1 0 0 1 0 1 0 0 0\n[End]'),
            ('bad.ts',v2+'[Mixed-Mode Order] D1,2 C1,2'),
            ('bad.ts',v2+'[Two-Port Data Order] 21_12\n[Reference] 50\n[Network Data]'),
            ('bad.ts',v2+'[Two-Port Data Order] 12_21\n[Network Data]\n\n[End]'),
            ('bad.ts',v2+'[Two-Port Data Order] 12_21\n[Network Data]\n1 0 0 0 0 0 0 0 0\n[End]\n[End]'),
            ('bad.s1p',v2),
            ('bad.s1p','a'*(1024**2+1)),
        ]
        for name,content in options:
            with self.subTest(name=name,excerpt=content[:35]), self.assertRaises((ValueError,ResourceLimitError)):
                read_touchstone(self.create(name,content))
        path=self.create('caught.s1p','# Hz S RI\n1 0 0')
        with self.assertRaises(ResourceLimitError):
            read_touchstone(path, context=ExecutionContext(max_work_bytes=5000))
        with self.assertRaises(ValueError):
            read_touchstone(self.folder)

    def test_export_refuses_loss_of_reference_information_and_is_atomic(self):
        destination=self.create('current.s2p', '# old\n')
        source=RFNetwork([1],np.ones((1,2,2)),reference_ohm=[50,100])
        with self.assertRaisesRegex(ValueError,'referencias'):
            write_touchstone(destination,source,version='1.0')
        spread=RFNetwork([1,2],np.ones((2,2,2)),reference_ohm=[[50,50],[50,75]])
        with self.assertRaisesRegex(ValueError,'referencias'):
            write_touchstone(destination,spread)
        event=threading.Event()
        class StopBeforeReplace(ExecutionContext):
            def checkpoint(self,percentage=None):
                calls.append(1)
                if len(calls)==3:event.set()
                return super().checkpoint(percentage)
        calls=[]
        with self.assertRaises(OperationCancelled):
            write_touchstone(destination,source,context=StopBeforeReplace(cancel=event))
        self.assertEqual(destination.read_text(), '# old\n')
        self.assertEqual(len(tuple(self.folder.iterdir())), 1)


class RFStorageTests(unittest.TestCase):
    def test_json_and_binary_project_preserve_rf_lineage_and_signal(self):
        project = Project()
        signal = project.add(Signal([3,2],-1,name='existing'))
        original=RFNetwork([90,300],[[[0,.7j],[.7j,0]],[[1,0],[0,1]]],name='Medición',
                           reference_ohm=[[40,50],[60,75]],metadata={'instrument':'example'})
        original_id=store_network(project,original,parents=(signal,),operation='RF test')
        converted=renormalize(original,[50,50])
        converted_id=store_network(project,converted,parents=(original_id,),settings={'reference_ohm':[50,50]})
        with TemporaryDirectory() as directory:
            for extension in ('json','slproj'):
                file=Path(directory)/f'session.{extension}'
                workspace=empty_workspace()
                save(file,project,workspace)
                if extension=='slproj':
                    self.assertTrue(file.read_bytes().startswith(MAGIC_RF))
                reopened,restored=load(file)
                self.assertEqual(restored,workspace)
                assert_array_equal(reopened.get(signal).values,[3,2])
                measured=load_network(reopened,original_id)
                assert_array_equal(measured.values,original.values)
                assert_array_equal(measured.reference_ohm,original.reference_ohm)
                assert_array_equal(measured.frequencies_hz,original.frequencies_hz)
                self.assertEqual(measured.metadata,original.metadata)
                assert_array_equal(load_network(reopened,converted_id).values,converted.values)
                self.assertEqual(reopened.headers('calculation')[1]['parents'],[original_id])
            old=Project();old.add(Signal([12]))
            file=Path(directory)/'legacy.slproj'
            save(file,old,empty_workspace())
            self.assertTrue(file.read_bytes().startswith(MAGIC))
            self.assertEqual(len(load(file)[0].headers('signal')),1)

    def test_binary_fingerprint_and_project_provenance_detect_distinct_corruption(self):
        project=Project()
        net=RFNetwork([1],[[[.5+.2j]]])
        document=encode_network(net)
        assert_array_equal(decode_network(document).values,net.values)
        for update in ({'schema':False}, {'frequency_unit':'GHz'}, {'wave_convention':'pseudo'},
                       {'data_base64':'abc'}, {'data_sha256':'0'*64}, {'ports':True}):
            with self.subTest(update=update),self.assertRaises(ValueError):
                decode_network(document|update)
        root=store_network(project,net)
        record=deepcopy(project._records[root])
        record['data']['metadata']['new']='test'
        with self.assertRaisesRegex(ValueError,'cambió'):
            Project.from_document({'format':'signallab-project','schema_version':2,'records':[record]})
        with self.assertRaisesRegex(ValueError,'red RF verificable'):
            load_network(project,project.add(document))
        with self.assertRaisesRegex(ValueError,'Origen'):
            store_network(project,net,parents=['missing'])


if __name__=='__main__':
    unittest.main()
