from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from signallab_pc.resources import _linux_memory_headroom, ensure_working_set, ResourceLimitError


class ResourceEnvelopeTests(unittest.TestCase):
    def test_cgroup_admission_respects_shared_ancestor_headroom(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            cgroup = root/'process.cgroup'
            cgroup.write_text('0::/group/worker\n', encoding='utf-8')
            hierarchy = root/'mounted'
            group = hierarchy/'group'
            leaf = group/'worker'
            leaf.mkdir(parents=True)
            for path, cap, used in ((hierarchy, 'max', 500), (group, 1000, 950), (leaf, 400, 120)):
                (path/'memory.max').write_text(str(cap), encoding='ascii')
                (path/'memory.current').write_text(str(used), encoding='ascii')
            measured = _linux_memory_headroom(cgroup, hierarchy)
            self.assertEqual(measured, 50)
            self.assertEqual(ensure_working_set(17, bytes_per_sample=1, live_arrays=1,
                                                available_bytes=measured), 17)
            with self.assertRaises(ResourceLimitError):
                ensure_working_set(18, bytes_per_sample=1, live_arrays=1, available_bytes=measured)
            (group/'memory.current').write_text('1100', encoding='ascii')
            self.assertEqual(_linux_memory_headroom(cgroup, hierarchy), 0)
