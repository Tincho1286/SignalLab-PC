"""Independent time-domain and FFT contrasts for the archived phase 04 candidate."""
import hashlib
import importlib.abc
import json
from pathlib import Path
import subprocess
import sys


class NoQt(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split('.')[0] in {'PySide6', 'PyQt6', 'shiboken6', 'qtpy'}:
            raise AssertionError(f'Qt import: {name}')


sys.meta_path.insert(0, NoQt())
import numpy as np
from scipy.stats import t
from signallab_pc.communications_fading import FadingPath, FadingSpec, apply_fading
from signallab_pc.model import Signal

SIZE, FS, FD, BINS = 32768, 4096, 64, 2048
LAGS = [16, 32, 64]
SEEDS = list(range(54001, 54033))
CANDIDATE = '2a0a3fd97e63bd766d09739d51dc9aab4e9e6efb'
ORACLES = {'covariance_complex_max_absolute_error': 0.08,
           'outer_welch_power_fraction_minimum': 0.99,
           'inner_welch_power_fraction_absolute_error': 0.04}


def audit(output):
    def git(*args):
        return subprocess.check_output(['git', *args], text=True).strip()

    assert git('rev-parse', 'HEAD') == CANDIDATE and not git('status', '--porcelain')
    source = Signal(np.ones(SIZE), metadata={'sample_rate_hz': FS})
    theta = 2*np.pi*np.arange(32768)/32768
    correlation_reference = np.mean(np.cos(2*np.pi*FD/FS*np.asarray(LAGS)[:, None]*np.cos(theta)), axis=1)
    freq = np.fft.fftfreq(BINS, 1/FS)
    window = .5 - .5*np.cos(2*np.pi*np.arange(BINS)/BINS)
    rows = []
    for seed in SEEDS:
        state, = apply_fading(source, FadingSpec((FadingPath(),), seed, FD)).realizations
        sample = state.coefficients.values
        corr = [np.vdot(sample[:-lag], sample[lag:])/(SIZE-lag) for lag in LAGS]
        blocks = np.lib.stride_tricks.sliding_window_view(sample, BINS)[::BINS//2]
        power_by_bin = np.mean(abs(np.fft.fft(blocks*window, axis=-1))**2, axis=0)
        rows.append([float(np.mean(abs(sample)**2)), *[v.real for v in corr], *[v.imag for v in corr],
                     np.sum(power_by_bin[abs(freq) <= FD/2])/np.sum(power_by_bin),
                     np.sum(power_by_bin[abs(freq) <= FD+2*FS/BINS])/np.sum(power_by_bin)])
    replicas = np.asarray(rows)
    means = replicas.mean(axis=0)
    stdev = replicas.std(axis=0, ddof=1)
    standard_error = stdev/np.sqrt(len(SEEDS))
    radius = t.ppf(.975, len(SEEDS)-1)*standard_error
    complex_mean = means[1:4] + 1j*means[4:7]
    checks = {
        'complex_covariance': bool(np.all(abs(complex_mean-correlation_reference) < ORACLES['covariance_complex_max_absolute_error'])),
        'inner_band': bool(abs(means[7]-1/3) < ORACLES['inner_welch_power_fraction_absolute_error']),
        'outer_band': bool(means[8] > ORACLES['outer_welch_power_fraction_minimum']),
    }
    names = ['sample_power', *[f'correlation_real_lag_{lag}' for lag in LAGS],
             *[f'correlation_imag_lag_{lag}' for lag in LAGS], 'inner_band_fraction', 'outer_band_fraction']
    document = {
        'commit': CANDIDATE, 'samples': SIZE, 'sample_rate_hz': FS, 'max_doppler_hz': FD, 'bins': BINS, 'seeds': SEEDS,
        'checks': checks, 'thresholds': ORACLES, 'qt_blocked': True, 'lags': LAGS,
        'reference': {'time_average_power': 1., 'correlation_real': correlation_reference.tolist(),
                      'correlation_imag': [0., 0., 0.], 'inner_band_fraction': 1/3},
        'columns': names, 'replicas': replicas.tolist(),
        'summary': {name: {'mean': means[i], 'std_between_records': stdev[i], 'stderr': standard_error[i],
                           'interval95_unadjusted': [means[i]-radius[i], means[i]+radius[i]]} for i, name in enumerate(names)},
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    Path(output).write_text(json.dumps(document, allow_nan=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'checks': checks, 'summary': document['summary']}, allow_nan=False))
    assert all(checks.values())


if __name__ == '__main__':
    audit(sys.argv[1])
