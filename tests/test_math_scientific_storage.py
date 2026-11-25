import hashlib
from pathlib import Path
import json
import struct
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

from numpy.testing import assert_array_equal

from signallab_pc.execution import ExecutionContext
from signallab_pc.jobs import OperationCancelled
from signallab_pc.model import Signal
from signallab_pc.resources import ResourceLimitError
from signallab_pc.scientific_storage import load_binary_signal, save_binary_signal


class ScientificStorageTests(unittest.TestCase):
    def test_complex_values_large_integer_origin_clock_and_metadata_roundtrip(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'record.slbin'
            original=Signal([1+2j,0,-3],2**61,units='índice',
                            metadata={'sample_rate_hz':8,'time_start_s':-.25,'amplitude_units':'V'})
            save_binary_signal(original,path)
            result=load_binary_signal(path)
            assert_array_equal(result.values,original.values)
            self.assertEqual((result.origin,result.units,result.metadata),
                             (original.origin,original.units,original.metadata))
            with self.assertRaises(ResourceLimitError):
                load_binary_signal(path,ExecutionContext(max_work_bytes=64))

    def test_tampering_truncation_and_header_bounds(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'record.slbin'
            save_binary_signal(Signal([1,2,3]),path)
            raw=path.read_bytes()
            mutated=bytearray(raw)
            mutated[-35] ^= 1
            for damaged, text in ((mutated,'integridad'),(raw[:-1],'tamaño'),
                                   (raw[:8]+b'\xff'*4+raw[12:],'cabecera')):
                with self.subTest(text=text):
                    path.write_bytes(damaged)
                    with self.assertRaisesRegex(ValueError,text):
                        load_binary_signal(path)

    def test_cancelled_replace_preserves_existing_file_and_cleans_temporary(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'record.slbin'
            save_binary_signal(Signal([17]),path)
            previous=path.read_bytes()
            cancel=Event()
            with patch('signallab_pc.atomic_file.os.fsync',side_effect=lambda _:cancel.set()):
                with self.assertRaises(OperationCancelled):
                    save_binary_signal(Signal([4,5]),path,ExecutionContext(cancel=cancel))
            self.assertEqual(path.read_bytes(),previous)
            self.assertEqual(list(Path(folder).iterdir()),[path])

    def test_binary_layout_is_interoperable_and_duplicate_fields_are_rejected(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'record.slbin'
            save_binary_signal(Signal([1.25 - 2j], -5), path)
            raw = path.read_bytes()
            self.assertEqual(raw[:8], b'SLPCBIN\x01')
            header_end = 12 + struct.unpack_from('<I', raw, 8)[0]
            self.assertEqual(struct.unpack('<dd', raw[header_end:-32]), (1.25, -2.0))
            self.assertEqual(hashlib.sha256(raw[:-32]).digest(), raw[-32:])

            header = b'{"count":1,' + raw[13:header_end]
            unsigned = raw[:8] + struct.pack('<I', len(header)) + header + raw[header_end:-32]
            path.write_bytes(unsigned + hashlib.sha256(unsigned).digest())
            with self.assertRaisesRegex(ValueError, 'claves repetidas'):
                load_binary_signal(path)

    def test_header_schema_and_truncation_fail_before_sample_materialization(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'record.slbin'
            save_binary_signal(Signal([1, 2]), path)
            raw = path.read_bytes()
            header_end = 12 + struct.unpack_from('<I', raw, 8)[0]
            header = json.loads(raw[12:header_end])
            self.assertEqual(header['count'], 2)
            cases = (({**header, 'count': 0}, 'Cantidad'),
                     ({**header, 'metadata': []}, 'tipos'),
                     ({**header, 'origin': float('inf')}, 'Constante'),
                     ({**header, 'unexpected': 3}, 'Esquema'))
            with patch('signallab_pc.scientific_storage.np.empty') as allocate:
                for fields, diagnostic in cases:
                    with self.subTest(diagnostic=diagnostic):
                        encoded = json.dumps(fields).encode()
                        unsigned = raw[:8] + struct.pack('<I', len(encoded)) + encoded + raw[header_end:-32]
                        path.write_bytes(unsigned + hashlib.sha256(unsigned).digest())
                        with self.assertRaisesRegex(ValueError, diagnostic):
                            load_binary_signal(path)
                path.write_bytes(raw[:header_end-1])
                with self.assertRaisesRegex(ValueError, 'incompleta'):
                    load_binary_signal(path)
                allocate.assert_not_called()

    def test_cancelled_read_exits_between_payload_blocks(self):
        from signallab_pc import jobs

        with TemporaryDirectory() as folder:
            path = Path(folder) / 'record.slbin'
            save_binary_signal(Signal([1] * 70000), path)
            event = Event()
            calls = 0

            def interrupt(_):
                nonlocal calls
                calls += 1
                if calls == 4:
                    event.set()

            with jobs.observe(interrupt), self.assertRaises(OperationCancelled):
                load_binary_signal(path, ExecutionContext(cancel=event))
            self.assertEqual(calls, 4)
            self.assertEqual(load_binary_signal(path).values.size, 70000)
