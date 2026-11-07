"""Update trust boundary: independent signatures, hostile metadata and handoff."""
import base64
from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Event
import unittest
from unittest.mock import Mock, patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from signallab_pc.update_manifest import (verify_manifest, UpdateError, FEED_URL,
    FILENAMES, REPOSITORY, version_tuple, timestamp)
from signallab_pc.update_download import download, Cancelled, fetch_release
from signallab_pc.installations import installed, receipt, MARKER, start_update


class Response(io.BytesIO):
    def __init__(self, data, url=FEED_URL, length=None):
        super().__init__(data); self.url = url; self.headers = {} if length is None else {'Content-Length': str(length)}

    def geturl(self):
        return self.url


class UpdateContracts(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate(); self.public = self.key.public_key().public_bytes_raw()
        self.now = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc); self.data = b'installer fixture\x00\x01'
        self.payload = dict(schema=1, channel='stable', version='2.0.0',
            published_at=self.now.isoformat().replace('+00:00', 'Z'),
            expires_at=(self.now + timedelta(days=30)).isoformat().replace('+00:00', 'Z'),
            notes='Nueva versión estable.', assets={})
        for target, template in FILENAMES.items():
            name = template.format(version='2.0.0')
            self.payload['assets'][target] = dict(name=name,
                url=f'https://github.com/{REPOSITORY}/releases/download/v2.0.0/{name}',
                size=len(self.data), sha256=hashlib.sha256(self.data).hexdigest())

    def encoded(self, payload=None):
        raw = json.dumps(payload or self.payload, separators=(',', ':')).encode()
        return json.dumps(dict(payload=base64.b64encode(raw).decode(),
            signature=base64.b64encode(self.key.sign(raw)).decode())).encode()

    def release(self):
        return verify_manifest(self.encoded(), key=self.public, now=self.now)

    def test_verified_release_preserves_platforms_version_and_notes(self):
        release = self.release()
        self.assertTrue(release.newer_than('1.9.99')); self.assertFalse(release.newer_than('2.0.0'))
        self.assertFalse(release.newer_than('2.0.1')); self.assertEqual(set(release.assets), set(FILENAMES))
        self.assertEqual(release.notes, self.payload['notes'])

    def test_changed_bytes_wrong_key_and_unsigned_payload_cannot_be_used(self):
        other = Ed25519PrivateKey.generate().public_key().public_bytes_raw()
        for value, key in [(self.encoded().replace(b'payload', b'payloaD'), self.public),
                           (self.encoded(), other), (json.dumps(self.payload).encode(), self.public)]:
            with self.subTest(value=value[:20]):
                with self.assertRaises(UpdateError): verify_manifest(value, key=key, now=self.now)
        envelope = json.loads(self.encoded()); raw = base64.b64decode(envelope['payload']).replace(b'2.0.0', b'9.0.0')
        envelope['payload'] = base64.b64encode(raw).decode()
        with self.assertRaises(UpdateError): verify_manifest(json.dumps(envelope).encode(), key=self.public, now=self.now)

    def test_even_signed_malformed_metadata_is_rejected(self):
        mutations = [('schema', True), ('channel', 'preview'), ('version', '../2.0.0'), ('version', '2.0.0-preview'),
                     ('published_at', '2026-11-07Z'), ('expires_at', '2025-01-01T00:00:00Z'),
                     ('expires_at', '2030-01-01T00:00:00Z'), ('notes', {}), ('assets', {})]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                row = json.loads(json.dumps(self.payload)); row[field] = value
                with self.assertRaises(UpdateError): verify_manifest(self.encoded(row), key=self.public, now=self.now)
        for field, value in [('url', 'https://evil.example/update.exe'), ('name', '../setup.exe'),
                             ('size', True), ('size', 2**40), ('sha256', 'f' * 63)]:
            with self.subTest(field=field):
                row = json.loads(json.dumps(self.payload)); row['assets']['windows-x86_64'][field] = value
                with self.assertRaises(UpdateError): verify_manifest(self.encoded(row), key=self.public, now=self.now)

    def test_expired_future_and_duplicate_fields_fail_closed(self):
        for now in (self.now - timedelta(hours=1), self.now + timedelta(days=31)):
            with self.assertRaises(UpdateError): verify_manifest(self.encoded(), key=self.public, now=now)
        data = self.encoded(); duplicate = data[:-1] + b',"signature":"duplicate"}'
        with self.assertRaises(UpdateError): verify_manifest(duplicate, key=self.public, now=self.now)
        for value in ('1.2', '1.2.-1', '01.2.3', '1.2.65536', '9' * 5000 + '.0.0'):
            with self.assertRaises(UpdateError): version_tuple(value)
        with self.assertRaises(UpdateError): timestamp('2026-11-07Z')

    def test_download_checks_size_hash_and_redirect_before_handoff(self):
        asset = self.release().assets['windows-x86_64']
        with tempfile.TemporaryDirectory() as folder:
            path = download(asset, folder, opener=lambda url: Response(self.data, url, len(self.data)))
            self.assertEqual(path.read_bytes(), self.data)
            for data, final, length in [(self.data + b'x', asset.url, None), (self.data[:-1], asset.url, None),
                    (b'x' * len(self.data), asset.url, None), (self.data, 'http://github.com/a', None),
                    (self.data, 'https://evil.example/a', None), (self.data, asset.url, 1)]:
                with self.subTest(final=final, length=length):
                    before = set(Path(folder).iterdir())
                    with self.assertRaises(UpdateError): download(asset, folder, opener=lambda url: Response(data, final, length))
                    self.assertEqual(set(Path(folder).iterdir()), before)

    def test_cancelled_download_is_removed_and_no_installer_is_started(self):
        asset = self.release().assets['windows-x86_64']; cancel = Event()
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(Cancelled):
                download(asset, folder, cancel=cancel, progress=lambda *_: cancel.set(), opener=lambda url: Response(self.data, url))
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_tampering_between_download_and_installation_is_detected(self):
        asset = self.release().assets['windows-x86_64']
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); exe = root / 'SignalLab-PC.exe'; exe.write_bytes(b'current')
            (root / MARKER).write_text(json.dumps(receipt('1.7.0', 'windows-x86_64', 'windows-user-v1')))
            context = installed(executable=exe, frozen=True); self.assertIsNotNone(context)
            candidate = root / asset.name; candidate.write_bytes(b'x' * len(self.data)); launch = Mock()
            with self.assertRaises(UpdateError): start_update(asset, candidate, context, launch=launch)
            launch.assert_not_called()
            candidate.write_bytes(self.data); start_update(asset, candidate, context, launch=launch)
            self.assertEqual(launch.call_args.args[0][0], str(candidate))
            self.assertIn('/DIR=' + str(root.resolve()), launch.call_args.args[0])
            self.assertFalse(launch.call_args.kwargs.get('shell', False))

    def test_portable_and_downgrade_do_not_start_an_installer(self):
        asset = self.release().assets['windows-x86_64']; launch = Mock()
        self.assertIsNone(installed(frozen=False))
        with self.assertRaises(UpdateError): start_update(asset, 'unused', None, launch=launch)
        from signallab_pc.installations import Installation
        for version in ('2.0.0', '2.0.1'):
            context = Installation(Path('unused'), 'windows-x86_64', version, Path('unused'))
            with self.assertRaises(UpdateError): start_update(asset, 'unused', context, launch=launch)
        launch.assert_not_called()

    def test_cache_cleanup_only_removes_registered_obsolete_update_files(self):
        from signallab_pc.update_cache import prune, MARKER
        asset = self.release().assets['windows-x86_64']
        with tempfile.TemporaryDirectory() as folder:
            path = download(asset, folder, opener=lambda url: Response(self.data, url))
            foreign = Path(folder) / 'signallab-update-my-project'; foreign.mkdir(); (foreign / 'notes.txt').write_text('keep')
            self.assertEqual(prune(folder,'1.7.0'),0); self.assertTrue(path.exists())
            self.assertEqual(prune(folder,'2.0.0'),1); self.assertFalse(path.exists())
            self.assertEqual((foreign / 'notes.txt').read_text(),'keep')
            path = download(asset, folder, opener=lambda url: Response(self.data, url))
            (path.parent / 'user-notes.txt').write_text('keep extra file')
            self.assertEqual(prune(folder,'2.0.0'),0); self.assertTrue(path.exists())

    def test_network_check_requires_the_signed_feed(self):
        release = fetch_release(opener=lambda url: Response(self.encoded(), url), key=self.public, now=self.now)
        self.assertEqual(release.version, '2.0.0')
        from urllib.error import HTTPError
        def missing(url): raise HTTPError(url, 404, 'missing', {}, None)
        with self.assertRaisesRegex(UpdateError, 'Todavía no hay'): fetch_release(opener=missing)

    def test_signing_tool_cannot_sign_using_an_unrelated_private_key(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import update_signing
        from cryptography.hazmat.primitives import serialization
        private = self.key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        with self.assertRaisesRegex(ValueError, 'no corresponde'): update_signing.sign('2.0.0', [], private, 'Notes')

    def test_offline_signer_binds_both_native_installer_proofs(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import update_signing
        from tools.distribution_receipt import source_fingerprint
        import subprocess
        from cryptography.hazmat.primitives import serialization
        private = self.key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); paths = []
            for tag, template in FILENAMES.items():
                path = root / template.format(version='2.0.0'); path.write_bytes(self.data); paths.append(path)
                proof = dict(version='2.0.0', filename=path.name, sha256=hashlib.sha256(self.data).hexdigest(),
                    size=len(self.data), source_fingerprint=source_fingerprint(),
                    source_commit=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip())
                (root / ('installer-' + tag.split('-')[0] + '.json')).write_text(json.dumps(proof))
            with patch.object(update_signing, 'public_key', return_value=self.public), patch.object(update_signing, 'APP_VERSION', '2.0.0'), patch('signallab_pc.update_manifest.public_key', return_value=self.public):
                data = update_signing.sign('2.0.0', paths, private, 'Authenticated notes', now=self.now)
                self.assertEqual(verify_manifest(data, key=self.public, now=self.now).notes, 'Authenticated notes')
                paths[0].write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'no coincide'): update_signing.sign('2.0.0', paths, private, 'Notes', now=self.now)

    def test_installer_archive_cannot_escape_the_staging_directory(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import build_installers, tarfile
        from signallab_pc import __version__
        prefix = 'SignalLab-PC-' + __version__ + '-linux-x86_64'
        for name, link in [(prefix + '/../outside', False), ('/absolute', False),
                           (prefix + '/C:escape', False), (prefix + '/link', True)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                root = Path(folder); archive = root / 'hostile.tar.gz'; destination = root / 'stage'; destination.mkdir()
                with tarfile.open(archive, 'w:gz') as package:
                    row = tarfile.TarInfo(name)
                    if link: row.type = tarfile.SYMTYPE; row.linkname = '../outside'
                    else: row.size = 1
                    package.addfile(row, None if link else io.BytesIO(b'x'))
                with self.assertRaises(ValueError): build_installers.extract_linux(archive, destination)
                self.assertEqual(list(destination.iterdir()), [])

    def test_handoff_uses_an_independent_runtime_without_mutating_the_parent_environment(self):
        from signallab_pc.process_handoff import launch_independent
        launch = Mock()
        with patch.dict(os.environ, {'LD_LIBRARY_PATH': '/old/extraction', 'LD_LIBRARY_PATH_ORIG': '/system/libs'}, clear=False), patch('signallab_pc.process_handoff.sys.platform', 'linux'):
            launch_independent(['/bin/sh', '/verified/installer.run'], launch=launch)
            env = launch.call_args.kwargs['env']
            self.assertEqual(env['PYINSTALLER_RESET_ENVIRONMENT'], '1'); self.assertEqual(env['LD_LIBRARY_PATH'], '/system/libs')
            self.assertEqual(os.environ['LD_LIBRARY_PATH'], '/old/extraction')


class UpdateUiContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_portable_never_starts_an_automatic_network_check(self):
        from PySide6.QtWidgets import QMainWindow
        from PySide6.QtCore import QSettings
        from signallab_pc.update_ui import UpdateController
        with tempfile.TemporaryDirectory() as folder:
            host = QMainWindow(); host.settings = QSettings(str(Path(folder) / 'settings.ini'), QSettings.Format.IniFormat); host._workers = []
            with patch('signallab_pc.update_ui.installed', return_value=None), patch('signallab_pc.update_ui.QTimer.singleShot') as schedule:
                controller = UpdateController(host); schedule.assert_not_called()
                self.assertFalse(controller.dialog.automatic.isChecked()); self.assertFalse(controller.dialog.automatic.isEnabled())
                self.assertFalse(controller.dialog.apply.isEnabled())
            controller.dialog.close(); host.close(); host.deleteLater(); self.app.processEvents()

    def test_help_menu_opens_updates_without_replacing_the_workspace(self):
        from signallab_pc.workbench import WorkbenchWindow
        with tempfile.TemporaryDirectory() as folder, patch('signallab_pc.update_ui.installed', return_value=None):
            from PySide6.QtCore import QSettings
            settings = QSettings(str(Path(folder) / 'settings.ini'), QSettings.Format.IniFormat)
            with patch('signallab_pc.workbench.QSettings', return_value=settings):
                window = WorkbenchWindow()
            actions = window.menuBar().actions()  # Keep the QAction wrappers alive while using their menus.
            menu = next(a for a in actions if a.text() == 'Ayuda').menu()
            action = next(a for a in menu.actions() if a.text() == 'Buscar actualizaciones…')
            page = window.stack.currentWidget(); action.trigger(); self.app.processEvents()
            self.assertTrue(window.updates.dialog.isVisible()); self.assertIs(window.stack.currentWidget(), page)
            window.updates.dialog.close(); window.close(); window.deleteLater(); self.app.processEvents()


if __name__ == '__main__': unittest.main()
