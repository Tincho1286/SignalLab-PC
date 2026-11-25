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
            with self.assertRaisesRegex(ValueError,'dimensiones'):
                reader.load('data/x')
