"""Plot data and render scientific communications views without Qt."""

import math

import numpy as np
from scipy.signal import freqz

from .dft_application import DFTRequest, calculate_dft
from .dsp_application import PSDRequest, estimate_psd
from .communications_metrics import theoretical_error
from .communications_sweep import AXES
from .signal_plot import configure_axis, plot_samples
from .theme_tokens import COLORS


def _selection(values, limit=4096):
    return values if len(values) <= limit else values[np.linspace(0, len(values)-1, limit, dtype=np.int64)]


def constellation_figure(figure, points, observations=(), units='1'):
    axis = figure.add_subplot(111)
    if len(points):
        points = _selection(points, 1024)
        axis.scatter(points.real, points.imag, s=26, facecolors='none', edgecolors=COLORS['blue'],
                     label='Constelación de referencia')
    if len(observations):
        observations = _selection(observations)
        axis.scatter(observations.real, observations.imag, s=10, alpha=.6, color=COLORS['green'],
                     label='Símbolos observados')
    axis.axhline(0, color=COLORS['grid'], lw=.8)
    axis.axvline(0, color=COLORS['grid'], lw=.8)
    axis.set(xlabel=f'I ({units})', ylabel=f'Q ({units})')
    axis.set_aspect('equal', adjustable='box')
    axis.legend()


def iq_figure(figure, signal):
    count = min(signal.values.size, 512)
    offsets = np.arange(count, dtype=np.int64)
    rate, start = signal.metadata.get('sample_rate_hz'), signal.metadata.get('time_start_s')
    horizontal = offsets + signal.origin
    xlabel = 'Índice n (muestras)'
    if rate is not None:
        horizontal = offsets / rate + (0 if start is None else start)
        xlabel = 'Tiempo (s)' if start is not None else 'Tiempo desde el inicio del registro (s)'
    values = signal.values[:count]
    units = signal.metadata.get('amplitude_units', '1')
    axes = figure.subplots(2, 1, sharex=True)
    for axis, component, color, title in (
        (axes[0], values.real, COLORS['blue'], 'I'), (axes[1], values.imag, COLORS['green'], 'Q'),
    ):
        # Index plots retain integer ticks and sample-based cursors.
        source = signal if rate is None else None
        plot_samples(axis, horizontal, component, discrete=True, color=color, source=source,
                     component='real' if title == 'I' else 'imag')
        axis.set_ylabel(f'{title} ({units})')
    configure_axis(axes[1], discrete_index=rate is None, label=xlabel)
    if count < signal.values.size:
        axes[0].set_title(f'Primeras {count} de {signal.values.size:,} muestras')


def eye_figure(figure, signal, sps, sample_offset, count):
    anchors = sample_offset + np.arange(count, dtype=np.int64)*sps
    anchors = _selection(anchors[(anchors >= sps) & (anchors < signal.values.size-sps)], 96)
    if not anchors.size:
        raise ValueError('Se necesitan muestras completas a ambos lados de un símbolo para abrir el ojo.')
    indices = np.arange(-sps, sps+1)
    horizontal = indices/sps
    axes = figure.subplots(2, 1, sharex=True)
    units = signal.metadata.get('amplitude_units', '1')
    for axis, part, color in ((axes[0], 'real', COLORS['blue']), (axes[1], 'imag', COLORS['green'])):
        for anchor in anchors:
            axis.plot(horizontal, getattr(signal.values[anchor+indices], part), color=color, alpha=.28, lw=.8)
        axis.axvline(0, color=COLORS['amber'], ls='--', lw=1)
        axis.set_ylabel(f'{"I" if part == "real" else "Q"} ({units})')
        axis.grid(alpha=.22)
    axes[-1].set_xlabel('Tiempo relativo al instante de decisión (períodos de símbolo)')
    axes[0].set_title(f'{len(anchors)} trazas centradas en los símbolos recuperados')


def spectrum_data(signal, *, density=False):
    if not density:
        return calculate_dft(DFTRequest(signal)).spectrum
    segment = min(1024, signal.values.size)
    return estimate_psd(PSDRequest(signal, segment=segment, overlap=segment//2))


def spectrum_figure(figure, spectrum, *, density=False):
    axis = figure.add_subplot(111)
    if density:
        x = spectrum.axis
        y = spectrum.values.real
        xlabel = 'Frecuencia (Hz)'
        ylabel = spectrum.metadata.get('density_units', 'Potencia/Hz')
    else:
        n = spectrum.values.size
        omega = spectrum.axis
        rate = spectrum.metadata.get('input_clock', {}).get('sample_rate_hz')
        x = omega if rate is None else omega * (rate/math.tau)
        y = abs(spectrum.values) / n
        xlabel = 'Frecuencia (rad/muestra)' if rate is None else 'Frecuencia (Hz)'
        ylabel = '|X[k]| / N'
    axis.plot(x, y, color=COLORS['blue'], lw=1)
    axis.set(xlabel=xlabel, ylabel=ylabel)
    axis.grid(alpha=.22)


def pulse_figure(figure, pulse):
    axis = figure.add_subplot(111)
    values = pulse.taps
    indices = _selection(np.arange(values.size))
    plot_samples(axis, indices, values[indices], discrete=True, color=COLORS['blue'])
    configure_axis(axis, discrete_index=True, label='Índice n (muestras)')
    axis.set_ylabel('h[n]')
    axis.set_title(f'{pulse.specification.family.upper()} · {values.size} coeficientes')


def filter_frequency_figure(figure, pulse):
    frequency, response = freqz(pulse.taps, worN=2048, include_nyquist=True)
    axes = figure.subplots(2, 1, sharex=True)
    magnitude = abs(response)
    axes[0].plot(frequency, magnitude, color=COLORS['blue'])
    axes[0].set_ylabel('|H|')
    phase = np.unwrap(np.angle(response))
    phase[magnitude < magnitude.max()*1e-12] = np.nan
    axes[1].plot(frequency, phase, color=COLORS['green'])
    axes[1].set_ylabel('Fase (rad)')
    configure_axis(axes[1], units='rad/muestra', label='ω (rad/muestra)')
    for axis in axes:
        axis.grid(alpha=.22)


def performance_figure(figure, specification, eb_n0_db, metrics):
    axis = figure.add_subplot(111)
    levels = np.linspace(eb_n0_db-6, eb_n0_db+6, 81)
    theory = [theoretical_error(specification, level) for level in levels]
    for field, color in (('ber', COLORS['blue']), ('ser', COLORS['green'])):
        rates = np.array([getattr(point, field) or np.nan for point in theory])
        reference = getattr(theory[0], field+'_reference')
        if np.isfinite(rates).any():
            label = 'aproximado' if reference == 'gray_nearest_neighbors' else 'teórico'
            axis.semilogy(levels, rates, color=color, label=f'{field.upper()} {label}')
        measured = getattr(metrics, field)
        if measured.value:
            axis.scatter([eb_n0_db], [measured.value], color=color, s=26, marker='o', label=f'{field.upper()} observado')
        elif measured.confidence is not None:
            axis.scatter([eb_n0_db], [measured.confidence.upper], color=color, marker='v',
                         label=f'Cota de {field.upper()}')
    if axis.lines or axis.collections:
        axis.set(yscale='log', xlabel='Eb/N₀ (dB)', ylabel='Tasa de error')
        axis.legend()
    else:
        axis.text(.5, .5, 'Sin tasa positiva ni cota estadística para mostrar en escala logarítmica.',
                  transform=axis.transAxes, ha='center', wrap=True)
        axis.set_axis_off()


def sweep_figure(figure, sweep):
    names = [axis.parameter for axis in sweep.specification.axes]
    horizontal = 'eb_n0_db' if 'eb_n0_db' in names else names[0]
    separate = [name for name in names if name != horizontal]
    groups = {}
    for row in sweep.runs:
        key = tuple(row['parameters'][name] for name in separate)
        groups.setdefault(key, []).append(row)
    axes = figure.subplots(3, 1, sharex=True)
    colors = [COLORS[color] for color in ('blue', 'green', 'amber', 'purple', 'red', 'cyan')]
    for group, (key, rows) in enumerate(groups.items()):
        label = ', '.join(f'{AXES[name]}={value:g}' for name, value in zip(separate, key, strict=True))
        ordered = sorted(rows, key=lambda row: row['parameters'][horizontal])
        x = np.array([row['parameters'][horizontal] for row in ordered])
        color = colors[group % len(colors)]
        for axis, field in zip(axes[:2], ('ber', 'ser'), strict=True):
            rates = [None if row['metrics'] is None else row['metrics'][field] for row in ordered]
            observed = [np.nan if rate is None or rate['value'] == 0 else rate['value'] for rate in rates]
            bound = [np.nan if rate is None or rate['value'] or rate['confidence'] is None
                     else rate['confidence']['upper'] for rate in rates]
            ideal = [np.nan if row['theoretical'] is None else row['theoretical'][field] or np.nan for row in ordered]
            approximation = any(row['theoretical'] is not None
                                and row['theoretical'][field+'_reference'] == 'gray_nearest_neighbors'
                                for row in ordered)
            suffix = ' · '+label if label else ''
            if np.isfinite(observed).any():
                axis.semilogy(x, observed, color=color, marker='o', label=f'{field.upper()} medido{suffix}')
            if np.isfinite(bound).any():
                axis.scatter(x, bound, color=color, marker='v', label=f'Cota {field.upper()}{suffix}')
            if np.isfinite(ideal).any():
                model = 'aproximado' if approximation else 'teórico'
                axis.semilogy(x, ideal, color=color, ls='--', label=f'{field.upper()} {model}{suffix}')
        evm = [np.nan if row['metrics'] is None or row['metrics']['evm']['percent'] is None
               else row['metrics']['evm']['percent'] for row in ordered]
        if np.isfinite(evm).any():
            axes[2].plot(x, evm, color=color, marker='o', label='EVM' + (' · '+label if label else ''))
    for axis, label in zip(axes, ('BER', 'SER', 'EVM (%)'), strict=True):
        axis.set_ylabel(label)
        axis.grid(alpha=.2)
        if axis.lines or axis.collections:
            if label != 'EVM (%)':
                axis.set_yscale('log')
            axis.legend()
        else:
            axis.text(.5, .5, 'Sin valores representables en esta escala', transform=axis.transAxes, ha='center')
    axes[-1].set_xlabel(AXES[horizontal])
