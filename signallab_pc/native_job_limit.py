"""Apply a memory limit to a dedicated reader process before native imports."""

import sys


def limit_worker_memory(max_bytes):
    if sys.platform == 'win32':
        return _windows_job(max_bytes)
    if sys.platform == 'linux':
        import resource

        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        effective = min(limit for limit in (max_bytes, soft, hard) if limit != resource.RLIM_INFINITY)
        resource.setrlimit(resource.RLIMIT_AS, (effective, effective))
        return None
    raise OSError('El lector MAT aislado requiere Windows o Linux.')


def _windows_job(max_bytes):
    import ctypes as c
    from ctypes import wintypes as w

    class BasicLimits(c.Structure):
        _fields_ = [
            ('process_time', c.c_longlong), ('job_time', c.c_longlong), ('flags', w.DWORD),
            ('work_set_min', c.c_size_t), ('work_set_max', c.c_size_t), ('active_limit', w.DWORD),
            ('affinity', c.c_size_t), ('priority', w.DWORD), ('scheduling', w.DWORD),
        ]

    class ExtendedLimits(c.Structure):
        _fields_ = [
            ('basic', BasicLimits), ('io', c.c_uint64 * 6), ('process_memory', c.c_size_t),
            ('job_memory', c.c_size_t), ('peak_process', c.c_size_t), ('peak_job', c.c_size_t),
        ]

    kernel = c.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateJobObjectW
    create.argtypes, create.restype = (c.c_void_p, w.LPCWSTR), w.HANDLE
    configure = kernel.SetInformationJobObject
    configure.argtypes, configure.restype = (w.HANDLE, c.c_int, c.c_void_p, w.DWORD), w.BOOL
    assign = kernel.AssignProcessToJobObject
    assign.argtypes, assign.restype = (w.HANDLE, w.HANDLE), w.BOOL
    current = kernel.GetCurrentProcess
    current.argtypes, current.restype = (), w.HANDLE
    close = kernel.CloseHandle
    close.argtypes, close.restype = (w.HANDLE,), w.BOOL
    limits = ExtendedLimits()
    limits.basic.flags = 0x100 | 0x8  # PROCESS_MEMORY and ACTIVE_PROCESS.
    limits.basic.active_limit = 1
    limits.process_memory = max_bytes
    job = create(None, None)
    if not job:
        raise c.WinError(c.get_last_error())
    if not configure(job, 9, c.byref(limits), c.sizeof(limits)) or not assign(job, current()):
        error = c.get_last_error()
        close(job)
        raise c.WinError(error)
    return job  # Owned by this short-lived process and released by Windows at exit.
