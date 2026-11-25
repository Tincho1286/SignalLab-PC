from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import h5py
from numpy.testing import assert_array_equal

from signallab_pc.input_files import read_json
from signallab_pc.matlab_import import MatlabFile, _local_dataset
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError


class InputIntegrityTests(unittest.TestCase):
    def test_json_validates_structure_and_budget_before_parse(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/'doc.json'
            path.write_text('{"nombre":"señal"}',encoding='utf-8-sig')
            self.assertEqual(read_json(path),{'nombre':'señal'})
            with patch('signallab_pc.input_files.ensure_working_set',side_effect=ResourceLimitError('budget')):
                with self.assertRaises(ResourceLimitError):
                    read_json(path)

    def test_ambiguous_json_leaves_project_unchanged(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/'project.json'
            path.write_text('{"format":"signallab-project","schema_version":2,"records":[],"records":[]}')
            project=Project()
            existing=project.add({'report':'preservado'})
            with self.assertRaisesRegex(ValueError,'repetidas'):
                project.merge(path)
            self.assertEqual(project.get(existing),{'report':'preservado'})

    def test_text_and_json_release_shared_admission_after_contention_or_invalid_data(self):
        from signallab_pc.execution import ExecutionContext, ResourcePool
        from signallab_pc.input_files import read_text

        with TemporaryDirectory() as directory:
            path = Path(directory)/'doc.json'
            source = '{"name":"signal","count":8}'
            path.write_text(source, encoding='utf-8')
            pool = ResourcePool(8*path.stat().st_size)
            with patch('signallab_pc.execution._PROCESS_POOL', pool):
                with ExecutionContext().reserve(1):
                    with self.assertRaisesRegex(ResourceLimitError, 'compartida'):
                        read_text(path)
                    with self.assertRaisesRegex(ResourceLimitError, 'compartida'):
                        read_json(path)
                self.assertEqual(read_json(path), {'name': 'signal', 'count': 8})
                path.write_text('{"broken":}', encoding='utf-8')
                with self.assertRaises(ValueError):
                    read_json(path)
                path.write_text(source, encoding='utf-8')
                self.assertEqual(read_text(path), source)

    def test_mat_v73_nested_dataset_and_changed_shape(self):
        with TemporaryDirectory() as directory:
            path=Path(directory)/'fixture.mat'
            with h5py.File(path,'w') as file:
                file['data/x']=[1,2,3]
            reader=MatlabFile(path)
            assert_array_equal(reader.load('data/x'),[1,2,3])
            with h5py.File(path,'r+') as file:
                with self.assertRaisesRegex(ValueError,'mismo archivo'):
                    _local_dataset(file,'data/missing',h5py)
                del file['data/x']
                file['data/x']=[1,2,3,4]
            with self.assertRaisesRegex(ValueError,'cambió.*selección'):
                reader.load('data/x')

    def test_mat_classic_compressed_and_hdf_numeric_selection(self):
        import numpy as np
        from scipy.io import savemat

        with TemporaryDirectory() as directory:
            path = Path(directory) / 'classic.mat'
            wanted = np.array([[1+2j, 3], [-1, 2-3j]])
            savemat(path, {'signal': wanted, 'text': 'ordinary text'}, do_compression=True)
            classic = MatlabFile(path)
            self.assertEqual(classic.entries, {'signal': (2, 2)})
            assert_array_equal(classic.load('signal'), wanted)

            path = Path(directory) / 'numeric.mat'
            with h5py.File(path, 'w', userblock_size=512) as file:
                file.create_dataset('signal', data=wanted.T, compression='gzip')
                file['scalar'] = 11
                file['external_reference'] = h5py.ExternalLink('separate.mat', '/signal')
                file.create_dataset('oversized', shape=(4_194_305,), dtype='c16', chunks=(1024,))
            native = MatlabFile(path)
            self.assertEqual(native.entries['scalar'], ())
            self.assertNotIn('external_reference', native.entries)
            assert_array_equal(native.load('signal'), wanted)
            self.assertEqual(native.load('scalar').item(), 11)
            with self.assertRaisesRegex(ResourceLimitError, '64 MiB'):
                native.load('oversized')

    def test_mat_timeout_releases_the_single_reader(self):
        from scipy.io import savemat

        with TemporaryDirectory() as directory:
            path = Path(directory) / 'ordinary.mat'
            savemat(path, {'signal': [1, 2]})
            with patch('signallab_pc.matlab_process.MAT_TIMEOUT_SECONDS', 0):
                with self.assertRaisesRegex(TimeoutError, 'lectura MAT'):
                    MatlabFile(path)
            assert_array_equal(MatlabFile(path).load('signal'), [[1, 2]])
