import hashlib
from pathlib import Path
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
