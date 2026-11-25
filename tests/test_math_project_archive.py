from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from numpy.testing import assert_array_equal

from signallab_pc import session
from signallab_pc.dft_application import DFTRequest, calculate_dft, store_dft
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.project_archive import MAGIC, load, save


class ProjectArchiveTests(unittest.TestCase):
    def test_complete_project_preserves_session_and_legacy_roundtrip(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            project = Project()
            source = Signal([1, 2j, -3.] * 1000, -4, metadata={'sample_rate_hz': 8, 'time_start_s': -.125})
            result = calculate_dft(DFTRequest(source))
            original, spectrum = store_dft(project, result, source=source)
            mode = {'tools': [], 'tabs': [['menu', 'Proyecto']], 'active': 0}
            binary, legacy = root/'run.slproj', root/'run.json'
            session.save(binary, project, mode)
            session.save(legacy, project, mode)
            self.assertTrue(binary.read_bytes().startswith(MAGIC))
            self.assertLess(binary.stat().st_size, legacy.stat().st_size * .4)
            archived, workspace = session.load(binary)
            self.assertEqual(workspace, mode)
            self.assertEqual(archived.document(), project.document())
            assert_array_equal(archived.get(original).values, source.values)
            assert_array_equal(archived.get(spectrum).values, result.spectrum.values)
            archived.save(legacy)
            restored, _ = session.load(legacy)
            self.assertEqual(restored.document(), project.document())
            merged = Project()
            self.assertEqual(merged.merge(binary), 2)
            loaded_source, loaded_result = merged.headers()
            self.assertNotEqual(loaded_source['id'], original)
            self.assertEqual(loaded_result['parents'], [loaded_source['id']])
            assert_array_equal(merged.get(loaded_result['id']).values, result.spectrum.values)

    def test_snapshot_copies_and_archive_validation_are_atomic(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            project, path = Project(), root/'run.slproj'
            source = Signal([3, 7, 11])
            record = project.add(source)
            source.values[:] = 42
            document = project.document()
            document['records'][0]['data']['values'][0][0] = -5
            assert_array_equal(project.get(record).values, [3, 7, 11])
            save(path, project)
            before = path.read_bytes()
            with patch('signallab_pc.atomic_file.os.replace', side_effect=OSError('disco')):
                with self.assertRaisesRegex(OSError, 'disco'):
                    save(path, project)
            self.assertEqual(path.read_bytes(), before)
            with self.assertRaises(OperationCancelled):
                def cancelled():
                    raise OperationCancelled()
                save(path, project, before_commit=cancelled)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(root.iterdir()), [path])
            broken = bytearray(before)
            broken[-33] ^= 1
            path.write_bytes(broken)
            with self.assertRaisesRegex(ValueError, 'integridad'):
                project.merge(path)
            self.assertEqual(len(project.headers()), 1)
            path.write_bytes(before[:-1])
            with self.assertRaisesRegex(ValueError, 'tamaño'):
                load(path)
