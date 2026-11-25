"""Exercise installed 2.0.0 → candidate inside a disposable GitHub runner."""

import os
from pathlib import Path
from shutil import copyfile
import subprocess
import sys
from urllib.request import urlopen

from signallab_pc.installations import installed, start_update
from signallab_pc.update_download import download, file_hash
from signallab_pc.update_manifest import MAX_MANIFEST, REPOSITORY, UpdateError, decode, strict_json, timestamp, verify_manifest


def verify_upgrade(candidate, asset, folder):
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('La instalación de auditoría se ejecuta en el runner descartable de GitHub.')
    fixture_version = '2.0.0'
    folder = Path(folder)
    asset_root = f'https://github.com/{REPOSITORY}/releases/download/v{fixture_version}'
    with urlopen(f'{asset_root}/SignalLab-updates.json', timeout=30) as response:
        old_envelope = response.read(MAX_MANIFEST + 1)
    # Validate only the historical fixture at its signed publication time.
    meta = strict_json(decode(strict_json(old_envelope)['payload']))
    stable = verify_manifest(old_envelope, now=timestamp(meta['published_at']), expected_version=fixture_version)
    stable_asset = stable.assets[asset.platform]
    old_installer = download(stable_asset, folder)
    home = folder/'home'
    home.mkdir()
    target = home/'installation'
    data = home/'user-data'
    data.mkdir()
    fixture = Path(__file__).resolve().parents[1]/'tests/fixtures/session-v3-dft-2.0.0.json'
    user_session = data/'my-session.json'
    copyfile(fixture, user_session)
    user_hash = file_hash(user_session)
    windows = sys.platform == 'win32'
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    if windows:
        env.update(APPDATA=str(data), LOCALAPPDATA=str(data))
        flags = ['/VERYSILENT', '/SP-', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOLAUNCH']
        install = [str(old_installer), *flags, '/DIR=' + str(target)]
        executable = target/'SignalLab-PC.exe'
    else:
        env.update(HOME=str(home), XDG_DATA_HOME=str(home/'data'),
                   XDG_CONFIG_HOME=str(data), XDG_CACHE_HOME=str(home/'cache'))
        install = ['/bin/sh', str(old_installer), '--headless', '--target', str(target)]
        executable = target/'current/SignalLab-PC'

    def launch_for_audit(command, **options):
        # The audit coordinator remains alive to check the receipt. No running
        # application needs to be waited on, and no product settings are changed.
        options['env'].update(env)
        if windows:
            flags = {'/SILENT', '/SIGNALLABPARENTPID=' + str(os.getpid())}
            command = [arg for arg in command if arg not in flags] + ['/VERYSILENT', '/NOLAUNCH', '/SUPPRESSMSGBOXES']
        else:
            command[command.index('--update')+1] = '0'
            command.append('--headless')
        return subprocess.Popen(command, **options)

    subprocess.run(install, env=env, check=True, timeout=180)
    before = installed(executable=executable, frozen=True)
    try:
        if before is None or before.version != fixture_version:
            raise RuntimeError('La instalación inicial no corresponde al instalador estable 2.0.0.')
        mismatch = folder/'invalid-installer'
        mismatch.write_bytes(b'archivo de prueba sin ejecutable')
        try:
            start_update(asset, mismatch, before, launch=launch_for_audit)
        except UpdateError:
            pass
        else:
            raise RuntimeError('Se aceptó una descarga incompatible antes de la instalación.')
        assert installed(executable=executable, frozen=True).version == fixture_version
        update = start_update(asset, candidate, before, launch=launch_for_audit)
        if update.wait(timeout=180) != 0:
            raise RuntimeError('Falló la instalación del candidato sobre la estable.')
        after = installed(executable=executable, frozen=True)
        assert after is not None and after.version == asset.version and after.root == before.root
        assert file_hash(user_session) == user_hash
        from signallab_pc import session
        project, _ = session.load(user_session)
        assert project.headers()
        check = folder/'updated-app.json'
        subprocess.run([str(executable), '--self-check', str(check)], env=env, check=True, timeout=180)
        diagnostic = strict_json(check.read_bytes())
        assert diagnostic['ok'] and diagnostic['frozen']
        return {'from': fixture_version, 'to': after.version, 'stable_sha256': stable_asset.sha256,
                'candidate_sha256': asset.sha256, 'session_preserved': True,
                'corrupt_download_rejected': True, 'native_handoff': True, 'in_place': True}
    finally:
        if windows and (target/'unins000.exe').is_file():
            subprocess.run([str(target/'unins000.exe'), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'],
                           env=env, check=True, timeout=90)
        elif not windows and executable.is_file():
            subprocess.run([str(executable), '--install-linux', '--headless', '--uninstall', '--target', str(target)],
                           env=env, check=True, timeout=90)
