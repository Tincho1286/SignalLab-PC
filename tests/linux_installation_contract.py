"""Native POSIX installation contracts; run explicitly in the Linux build job."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from signallab_pc.linux_installation import install, uninstall
from signallab_pc.installations import installed, MARKER, read_receipt
from signallab_pc.update_manifest import UpdateError


class LinuxInstallationContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.base = Path(self.temp.name)
        self.home = self.base / 'home'; self.home.mkdir(); self.source = self.base / 'source'; self.source.mkdir()
        self.root = self.home / '.local/share/SignalLab-PC'; self.data = self.home / '.local/share'
        self.settings = self.home / '.config/SignalLab/test.ini'; self.settings.parent.mkdir(parents=True)
        self.settings.write_text('user-theme=dark\nimportant-data=keep\n')

    def tearDown(self):
        self.temp.cleanup()

    def payload(self, tag):
        header = bytearray(64); header[:6] = b'\x7fELF\x02\x01'; header[18:20] = (62).to_bytes(2, 'little')
        (self.source / 'SignalLab-PC').write_bytes(header + tag.encode())
        (self.source / 'LICENSE').write_text('fixture license')
        (self.source / 'signallab.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')

    def put(self, version, **options):
        self.payload(version)
        return install(self.source, self.root, version, home=self.home, data_home=self.data, **options)

    def test_upgrade_reuses_installation_preserves_settings_and_limits_old_versions(self):
        first = self.put('1.0.0'); self.assertTrue(first.is_file())
        second = self.put('1.0.1'); self.assertEqual((self.root / 'previous').resolve(), first.parent)
        latest = self.put('1.0.2')
        self.assertEqual((self.root / 'current').resolve(), latest.parent)
        self.assertEqual((self.root / 'previous').resolve(), second.parent)
        self.assertEqual(len(list((self.root / 'versions').iterdir())), 2)
        self.put('1.0.2')  # Repairing the current version must retain its predecessor.
        self.assertTrue(second.exists()); self.assertFalse(first.exists())
        self.assertEqual(read_receipt(self.root)['version'], '1.0.2')
        self.assertEqual(installed(executable=latest, frozen=True).version, '1.0.2')
        self.assertEqual(self.settings.read_text(), 'user-theme=dark\nimportant-data=keep\n')
        self.assertEqual((self.home / '.local/bin/signallab-pc').resolve(), latest)
        self.assertIn('Desktop Action Uninstall', (self.data / 'applications/org.signallab.PC.desktop').read_text())

    def test_failed_activation_preserves_old_release_previous_link_and_registration(self):
        first = self.put('1.0.0'); second = self.put('1.0.1')
        original = (self.data / 'applications/org.signallab.PC.desktop').read_bytes()
        def fail(*_): raise OSError('simulated activation failure')
        with self.assertRaises(OSError): self.put('1.0.2', activate=fail)
        self.assertEqual((self.root / 'current').resolve(), second.parent)
        self.assertEqual((self.root / 'previous').resolve(), first.parent)
        self.assertEqual(read_receipt(self.root)['version'], '1.0.1')
        self.assertEqual((self.data / 'applications/org.signallab.PC.desktop').read_bytes(), original)
        self.assertFalse(list((self.root / 'versions').glob('.pending-*')))

    def test_downgrade_unmanaged_roots_and_payload_symlinks_are_rejected(self):
        current = self.put('2.0.0')
        with self.assertRaises(UpdateError): self.put('1.9.9')
        self.assertEqual((self.root / 'current').resolve(), current.parent)
        foreign = self.home / 'my-project'; foreign.mkdir(); (foreign / 'data.txt').write_text('keep')
        with self.assertRaises(UpdateError): install(self.source, foreign, '2.0.1', home=self.home, data_home=self.data)
        (self.source / 'external-link').symlink_to(self.settings)
        with self.assertRaises(UpdateError): install(self.source, self.root, '2.0.1', home=self.home, data_home=self.data)
        self.assertEqual(self.settings.read_text(), 'user-theme=dark\nimportant-data=keep\n')
        self.assertEqual((foreign / 'data.txt').read_text(), 'keep')

    def test_uninstall_removes_managed_files_but_keeps_user_data(self):
        self.put('1.0.0'); self.put('1.0.1')
        note = self.root / 'my-notes.txt'; note.write_text('do not delete')
        uninstall(self.root, home=self.home, data_home=self.data)
        self.assertFalse((self.root / 'versions').exists()); self.assertFalse((self.root / 'current').is_symlink())
        self.assertFalse((self.home / '.local/bin/signallab-pc').is_symlink())
        self.assertFalse((self.data / 'applications/org.signallab.PC.desktop').exists())
        self.assertEqual(note.read_text(), 'do not delete'); self.assertTrue(self.settings.exists())


if __name__ == '__main__':
    if sys.platform != 'linux': raise SystemExit('Run these contracts on native Linux.')
    unittest.main()
