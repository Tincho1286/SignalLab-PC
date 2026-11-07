"""Start an independent program without inheriting a one-file extraction directory."""
import os
import subprocess
import sys


def independent_environment():
    env = dict(os.environ); env['PYINSTALLER_RESET_ENVIRONMENT'] = '1'
    if sys.platform == 'linux':
        original = env.get('LD_LIBRARY_PATH_ORIG')
        if original is None:
            env.pop('LD_LIBRARY_PATH', None)
        else:
            env['LD_LIBRARY_PATH'] = original
    return env


def launch_independent(command, *, launch=subprocess.Popen, **kwargs):
    """The Windows bootloader's DLL directory also needs temporary restoration."""
    reset_dll = sys.platform == 'win32' and getattr(sys, 'frozen', False)
    if reset_dll:
        import ctypes
        set_directory = ctypes.windll.kernel32.SetDllDirectoryW
        set_directory.argtypes = [ctypes.c_wchar_p]; set_directory.restype = ctypes.c_int
        if not set_directory(None):
            raise OSError('Windows no pudo preparar el instalador independiente.')
    try:
        return launch(command, env=independent_environment(), **kwargs)
    finally:
        if reset_dll:
            set_directory(getattr(sys, '_MEIPASS', None))
