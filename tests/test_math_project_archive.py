from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

from numpy.testing import assert_array_equal

from signallab_pc import session
from signallab_pc.dft_application import DFTRequest, calculate_dft, store_dft
from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.project_archive import MAGIC, load, save
from signallab_pc.resources import ResourceLimitError


class ProjectArchiveTests(unittest.TestCase):
    @staticmethod
    def archive(manifest, samples=b''):
        header = manifest if isinstance(manifest, bytes) else json.dumps(manifest).encode('utf-8')
        content = MAGIC + struct.pack('<I', len(header)) + header + samples
        return content + sha256(content).digest()

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

    def test_external_catalog_rejects_inconsistent_references_before_publication(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'external.slproj'
            target = Project()
            keep = target.add(Signal([9]))
            writer = Project()
            identifier = writer.add(Signal([2+3j]))
            catalog = writer.document()
            row = catalog['records'][0]
            row['data'].pop('values')
            body = struct.pack('<dd', 2, 3)
            read_cases = [
                (b'SLPROJ\x00\x02' + b'\0'*40, 'Formato'),
                (self.archive(b'{"project":{},"project":{},"workspace":null,"counts":[]}'), 'claves repetidas'),
                (self.archive(b'{"project":{},"workspace":{"a":NaN},"counts":[]}'), 'Constante JSON'),
                (self.archive(b'{"project":{},"workspace":{"a":1e99999},"counts":[]}'), 'números finitos'),
                (self.archive({'project': catalog, 'counts': [1]}), 'Manifiesto'),
                (self.archive({'project': catalog, 'workspace': None, 'counts': []}), 'catálogo'),
                (self.archive({'project': catalog, 'workspace': None, 'counts': [True]}), 'Referencia'),
                (self.archive({'project': catalog, 'workspace': None, 'counts': [0]}), 'referencia binaria'),
                (self.archive({'project': catalog, 'workspace': None, 'counts': [2**60]}), 'tamaño'),
                (self.archive({'project': {**catalog, 'records': [dict(row, kind='calculation')]},
                               'workspace': None, 'counts': [1]}, body), 'registros de señal'),
                (self.archive({'project': {**catalog, 'records': [dict(row, parents=['missing'])]},
                               'workspace': None, 'counts': [1]}, body), 'Procedencia'),
                (self.archive({'project': {**catalog, 'records': [row, row]},
                               'workspace': None, 'counts': [1, 1]}, body*2), 'repetidos'),
                (self.archive({'project': {**catalog, 'schema_version': 17},
                               'workspace': None, 'counts': [1]}, body), 'incompatible'),
            ]
            for contents, reason in read_cases:
                with self.subTest(reason=reason):
                    path.write_bytes(contents)
                    with self.assertRaisesRegex(ValueError, reason):
                        target.merge(path)
                    self.assertEqual([r['id'] for r in target.headers()], [keep])
            path.write_bytes(self.archive({'project': catalog, 'workspace': None, 'counts': [1]}, body))
            parsed, workspace = load(path)
            self.assertIsNone(workspace)
            assert_array_equal(parsed.get(identifier).values, [2+3j])

    def test_disk_and_permission_failures_leave_valid_checkpoint_and_allow_retry(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'recovery.slproj'
            project = Project()
            record = project.add(Signal([3]))
            save(path, project)
            old = path.read_bytes()
            project.add(Signal([4]))
            disk_usage = namedtuple('DiskUsage', 'total used free')
            with patch('signallab_pc.project_archive.disk_usage', return_value=disk_usage(1, 1, 0)):
                with self.assertRaisesRegex(ResourceLimitError, 'disco'):
                    save(path, project)
            with patch('signallab_pc.atomic_file.tempfile.mkstemp', side_effect=PermissionError('acceso')):
                with self.assertRaises(PermissionError):
                    save(path, project)
            self.assertEqual(path.read_bytes(), old)
            self.assertEqual(list(path.parent.iterdir()), [path])
            self.assertEqual(load(path)[0].get(record).values[0], 3)
            save(path, project)
            self.assertEqual(len(load(path)[0].headers()), 2)

    def test_snapshot_is_stable_and_validation_can_be_cancelled_after_binary_read(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'snapshot.slproj'
            project = Project()
            parent, child = store_dft(project, calculate_dft(DFTRequest(Signal([2, 5]))), source=Signal([2, 5]))
            snapshot = project.snapshot()
            project.add(Signal([7]), parents=[child])
            save(path, snapshot)
            before = path.read_bytes()

            checks = 0

            def abort_before_publication():
                nonlocal checks
                checks += 1
                if checks == 7:  # Both payloads were read and the catalog is being validated.
                    raise OperationCancelled()

            with self.assertRaises(OperationCancelled):
                load(path, checkpoint=abort_before_publication)
            self.assertEqual(path.read_bytes(), before)
            reopened, _ = load(path)
            self.assertEqual([row['id'] for row in reopened.headers()], [parent, child])
            assert_array_equal(reopened.get(child).values, [-3, 7])

    def test_parallel_calculation_and_archive_share_admission_and_release_on_error(self):
        with TemporaryDirectory() as folder:
            path = Path(folder)/'shared.slproj'
            project = Project()
            identifier = project.add({'expression': '2+3*i'}, title='Expresión')
            ctx = ExecutionContext()
            ready, finish = Event(), Event()

            def fail_after_reserving():
                ready.set()
                if not finish.wait(5):
                    raise TimeoutError()
                raise OperationCancelled()

            with patch('signallab_pc.execution.available_physical_memory', return_value=8*1024**2):
                with ThreadPoolExecutor() as worker:
                    future = worker.submit(ctx.run, fail_after_reserving, work_bytes=2*1024**2)
                    try:
                        self.assertTrue(ready.wait(5))
                        with self.assertRaisesRegex(ResourceLimitError, 'compartida'):
                            save(path, project)
                        self.assertFalse(path.exists())
                    finally:
                        finish.set()
                    with self.assertRaises(OperationCancelled):
                        future.result(timeout=2)
                save(path, project)
                reopened, _ = load(path)
                self.assertEqual(reopened.get(identifier), {'expression': '2+3*i'})
