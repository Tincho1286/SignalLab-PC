"""Generate independent numerical references for Phase 03 communications tests."""

import argparse
import json
from math import cos, exp, pi, sqrt
from pathlib import Path

from scipy.integrate import quad


def inverse_pulse(rolloff, time, *, root):
    """Integrate the even, unit-period ideal spectrum on its compact support."""
    edge = (1 - rolloff) / 2

    def kernel(frequency):
        return cos(2 * pi * frequency * time)

    plateau = quad(kernel, 0, edge, epsabs=2e-13, epsrel=2e-13)[0]
    transition = 0.0
    if rolloff:
        power = 1 if root else 2

        def integrand(frequency):
            weight = cos(pi * (frequency - edge) / (2 * rolloff))
            return weight**power * kernel(frequency)

        transition = quad(integrand, edge, edge + rolloff, epsabs=2e-13, epsrel=2e-13)[0]
    return 2 * (plateau + transition)


def reflected_words(width):
    words = ['']
    for _ in range(width):
        words = ['0' + word for word in words] + ['1' + word for word in reversed(words)]
    return words


def antipodal_ber(db):
    threshold = sqrt(2 * 10**(db / 10))
    return quad(lambda z: exp(-z*z/2) / sqrt(2*pi), threshold, float('inf'),
                epsabs=1e-16, epsrel=2e-13)[0]


def reference_report():
    pulses = []
    for rolloff in (0.0, 0.2, 0.25, 0.5, 1.0):
        for kind in ('rc', 'rrc'):
            times = {0.0, 0.125, 0.5, 1.0, 2.0, 3.125}
            if rolloff:
                pole = 1 / ((4 if kind == 'rrc' else 2) * rolloff)
                times.update((pole - 1e-7, pole, pole + 1e-7))
            samples = [[time, inverse_pulse(rolloff, time, root=kind == 'rrc')]
                       for time in sorted(times)]
            pulses.append({'kind': kind, 'rolloff': rolloff, 'samples': samples})
    return {
        'schema': 1,
        'pulse_method': 'quadrature of the ideal spectrum with symbol period 1',
        'pulses': pulses,
        'gray_cycle_8': reflected_words(3),
        'gray_axis_4': reflected_words(2),
        'square_qam_raw_energy': [[side**2, 2*sum((2*i-side+1)**2 for i in range(side))/side]
                                  for side in (2, 4, 8, 16)],
        'antipodal_ber': [[db, antipodal_ber(db)] for db in (-3, 0, 4, 8, 12)],
    }


def compare_komm(report):
    """Compare the spectral oracle with an optional external development tool."""
    import komm
    import numpy as np

    discrepancies = []
    for pulse in report['pulses']:
        model = komm.RaisedCosinePulse(pulse['rolloff'])
        is_root = pulse['kind'] == 'rrc'
        if is_root:
            model = model.root()
        times, reference = np.asarray(pulse['samples']).T
        errors = np.abs(model.waveform(times) - reference)
        near = np.zeros(times.size, dtype=bool)
        if pulse['rolloff']:
            pole = 1 / ((4 if is_root else 2) * pulse['rolloff'])
            near = (times != pole) & (np.abs(times - pole) < 2e-7)
        discrepancies.append({
            'kind': pulse['kind'], 'rolloff': pulse['rolloff'],
            'max_abs_difference': float(errors.max()),
            'max_abs_difference_at_other_points': float(errors[~near].max()),
            'max_abs_difference_beside_pole': float(errors[near].max()) if near.any() else None,
        })
    gray = [''.join(str(bit) for bit in word) for word in komm.ReflectedLabeling(3).matrix]
    return {
        'komm_version': komm.__version__,
        'numpy_version': np.__version__,
        'gray_cycle_8_matches': gray == report['gray_cycle_8'],
        'qam_raw_energy_matches': all(komm.QAMConstellation(order).mean_energy() == energy
                                      for order, energy in report['square_qam_raw_energy']),
        'pulse_comparison': discrepancies,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compare-komm', action='store_true')
    args = parser.parse_args()
    report = reference_report()
    if args.compare_komm:
        report = compare_komm(report)
    with args.output.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
