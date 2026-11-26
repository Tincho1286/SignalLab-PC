"""Plot data and render scientific communications views without Qt."""

import math

import numpy as np
from scipy.signal import freqz

from .dft_application import DFTRequest, calculate_dft
from .dsp_application import PSDRequest, estimate_psd
from .communications_metrics import theoretical_error
from .communications_sweep import axis_label, summarize_sweep_repetitions
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


def interference_spectra_figure(figure, records):
    axis = figure.add_subplot(111)
    rate = records[0][1].metadata.get('input_clock', {}).get('sample_rate_hz')
    for (label, spectrum), token in zip(records, ('blue', 'amber', 'green', 'muted')):
        coordinate = spectrum.axis if rate is None else spectrum.axis * (rate/math.tau)
        axis.plot(coordinate, abs(spectrum.values)/spectrum.values.size, label=label, color=COLORS[token])
    units = 'rad/muestra' if rate is None else 'Hz'
    configure_axis(axis, units=units, label=f'Frecuencia ({units})')
    axis.set_ylabel('|X[k]| / N')
    axis.grid(alpha=.22)
    axis.legend()


def pulse_figure(figure, pulse):
    axis = figure.add_subplot(111)
    values = pulse.taps
    indices = _selection(np.arange(values.size))
    plot_samples(axis, indices, values[indices], discrete=True, color=COLORS['blue'])
    configure_axis(axis, discrete_index=True, label='Índice n (muestras)')
    axis.set_ylabel('h[n]')
    axis.set_title(f'{pulse.specification.family.upper()} · {values.size} coeficientes')


def channel_taps_figure(figure, *, analysis):
    delays = np.array([tap.delay_samples for tap in analysis.taps], dtype=np.int64)
    gains = np.array([tap.gain for tap in analysis.taps])
    powers = np.array([row.power for row in analysis.power_delay_profile])
    axes = figure.subplots(3, 1, sharex=True)
    for axis, values, label, color in zip(
        axes, (gains.real, gains.imag, powers), ('Re h[n]', 'Im h[n]', 'Potencia'),
        (COLORS['blue'], COLORS['green'], COLORS['amber']), strict=True,
    ):
        plot_samples(axis, delays, values, discrete=True, color=color)
        axis.set_ylabel(label)
    configure_axis(axes[-1], discrete_index=True, label='Retardo (muestras)')


def channel_frequency_figure(figure, response):
    axes = figure.subplots(2, 1, sharex=True)
    values = response.values
    axes[0].plot(response.axis, abs(values), color=COLORS['blue'])
    phase = np.where(abs(values) > 16*np.finfo(float).eps * np.max(abs(values)), np.angle(values), np.nan)
    plot_samples(axes[1], response.axis, phase, phase=True, color=COLORS['green'])
    axes[0].set_ylabel('|H(eʲω)|')
    axes[1].set_ylabel('Fase (rad)')
    configure_axis(axes[1], units=response.units, label='ω (rad/muestra)')


def fading_envelope_figure(figure, *, result):
    axis = figure.add_subplot(111)
    for index, item in enumerate(result.realizations, 1):
        values = item.coefficients.values
        indices = np.linspace(0, len(values)-1, min(len(values), 2048), dtype=np.int64)
        arrival = indices + item.path.delay_samples
        axis.plot(arrival, abs(values[indices]), lw=1, label=f'Trayectoria {index}')
    configure_axis(axis, discrete_index=True, label='Muestras desde el comienzo del registro')
    axis.set_ylabel('|a[n]|')
    axis.legend()


def doppler_diagnostics_figure(figure, data, *, path_number, fd):
    corr, spectrum = figure.subplots(2, 1)
    lag = data.lags_samples / data.sample_rate_hz
    corr.plot(lag, data.observed_correlation.real, color=COLORS['blue'], label='Real observada')
    corr.plot(lag, data.theoretical_correlation, '--', color=COLORS['amber'], label='Clarke')
    corr.set(xlabel='Retardo (s)', ylabel='Correlación normalizada', title=f'Trayectoria {path_number}')
    spectrum.plot(data.frequencies_hz, data.observed_psd, color=COLORS['blue'], label='Welch')
    spectrum.step(data.frequencies_hz, data.theoretical_psd, where='mid', linestyle='--',
                  color=COLORS['amber'], label='Clarke por bin')
    spectrum.set(xlabel='Frecuencia Doppler (Hz)', ylabel='PSD normalizada (1/Hz)')
    radius = min(data.sample_rate_hz/2, fd + 5*data.sample_rate_hz/len(data.frequencies_hz))
    spectrum.set_xlim(-radius, radius)
    for axis in (corr, spectrum):
        axis.grid(alpha=.22)
        axis.legend()


def phase_path_figure(figure, *, signal):
    axis = figure.add_subplot(111)
    points = np.linspace(0, signal.values.size-1, min(signal.values.size, 4096), dtype=np.int64)
    rate = signal.metadata.get('sample_rate_hz')
    if rate is None:
        plot_samples(axis, points, signal.values.real[points], discrete=True, color=COLORS['blue'])
        configure_axis(axis, discrete_index=True, label='Muestras desde el comienzo del registro')
    else:
        plot_samples(axis, points/rate, signal.values.real[points], discrete=True, color=COLORS['blue'])
        axis.set_xlabel('Tiempo desde el comienzo del registro (s)')
    axis.set_ylabel('Fase (rad)')
    axis.grid(alpha=.22)


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
    rows_to_plot = sweep.runs
    if sweep.specification.repetitions > 1:
        rows_to_plot = []
        for point in summarize_sweep_repetitions(sweep):
            values = point['measurements']
            metrics = {
                name: {'value': values[name]['mean'], 'confidence': values[name]['confidence']}
                for name in ('ber', 'ser')
            }
            metrics['evm'] = {'percent': values['evm']['mean']}
            rows_to_plot.append({**point, 'metrics': metrics})
    for row in rows_to_plot:
        key = tuple(row['parameters'][name] for name in separate)
        groups.setdefault(key, []).append(row)
    axes = figure.subplots(3, 1, sharex=True)
    colors = [COLORS[color] for color in ('blue', 'green', 'amber', 'purple', 'red', 'cyan')]
    for group, (key, rows) in enumerate(groups.items()):
        label = ', '.join(f'{axis_label(name)}={value:g}' for name, value in zip(separate, key, strict=True))
        ordered = sorted(rows, key=lambda row: row['parameters'][horizontal])
        x = np.array([row['parameters'][horizontal] for row in ordered])
        color = colors[group % len(colors)]
        for axis, field in zip(axes[:2], ('ber', 'ser'), strict=True):
            rates = [None if row['metrics'] is None else row['metrics'][field] for row in ordered]
            observed = [np.nan if rate is None or not rate['value'] else rate['value'] for rate in rates]
            bound = [np.nan if rate is None or rate['value'] or rate['confidence'] is None
                     else rate['confidence']['upper'] for rate in rates]
            ideal = [np.nan if row['theoretical'] is None else row['theoretical'][field] or np.nan for row in ordered]
            approximation = any(row['theoretical'] is not None
                                and row['theoretical'][field+'_reference'] == 'gray_nearest_neighbors'
                                for row in ordered)
            suffix = ' · '+label if label else ''
            if np.isfinite(observed).any():
                axis.semilogy(x, observed, color=color, marker='o', label=f'{field.upper()} medido{suffix}')
                if sweep.specification.repetitions > 1:
                    for coordinate, value, rate in zip(x, observed, rates, strict=True):
                        if np.isfinite(value) and (interval := rate['confidence']) and interval['lower'] > 0:
                            axis.vlines(coordinate, interval['lower'], interval['upper'], color=color, alpha=.5)
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
    axes[-1].set_xlabel(axis_label(horizontal))
