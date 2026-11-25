"""Shared reconstruction of a figure from stored signal values."""

from copy import copy

import numpy as np

from .distributions import dirac_terms
from .probe_data import attach_signal
from .signal_plot import configure_axis, configure_signal_axis, is_discrete_plot, plot_impulse_areas, plot_samples
from .uniform_axis import sample_coordinate


def centered_bins_view(signal):
    view = copy(signal)
    view.origin = -(signal.values.size // 2)
    view.step = 1
    view.domain = 'discrete'
    view.units = 'k'
    return view


def polar_label(signals):
    return 'Densidad y dB' if all(signal.metadata.get('operation') in ('spectral_density', 'energy_density')
                                 for signal in signals) else 'Módulo y fase'


def draw_signal_figure(figure, signals, *, polar, select_indices):
    figure.clear()
    if all(signal.metadata.get('operation') == 'spectral_fraction' for signal in signals):
        draw_fraction(figure.add_subplot(111), signals)
        return
    impulses = [dirac_terms(signal) for signal in signals]
    if all(source.metadata.get('lines_only') for source in signals):
        axis = figure.add_subplot(111)
        for source, terms in zip(signals, impulses):
            plot_impulse_areas(axis, terms, source.name)
        configure_signal_axis(axis, signals[0])
        edges = [sample_coordinate(source, index) for source in signals for index in (0, source.values.size - 1)]
        if min(edges) < max(edges):
            axis.set_xlim(min(edges), max(edges))
        axis.set(ylabel='Área Dirac', title='Impulsos ideales')
        axis.grid(alpha=.2)
        if axis.get_legend_handles_labels()[0]:
            axis.legend()
        else:
            axis.text(.5,.5,'No hay impulsos en esta ventana',ha='center',transform=axis.transAxes)
        return
    has_delay = polar and all(source.metadata.get('operation') == 'frequency_filter' for source in signals)
    density = polar_label(signals) == 'Densidad y dB'
    axes = figure.subplots(2 + int(has_delay) + int(any(impulses)), 1, sharex=True)
    reduced = False
    for source, terms in zip(signals, impulses):
        shown = select_indices(source.values)
        reduced = reduced or shown.size < source.values.size
        values = source.values[shown]
        x = int(source.origin) + shown if source.domain == 'discrete' else source.origin + source.step * shown
        discrete = is_discrete_plot(source)
        if polar and density:
            first = values.real
            second = np.full(values.size, np.nan)
            second[first > 0] = 10 * np.log10(first[first > 0])
        elif polar:
            first = np.abs(values)
            second = np.where(first > 0, np.angle(values), np.nan)
        else:
            first, second = values.real, values.imag
        plot_samples(axes[0], x, first, discrete=discrete, label=source.name, source=source,
                     component='magnitude' if polar and not density else 'real')
        valid = np.isfinite(second)
        if np.any(valid):
            kind = 'density_db' if polar and density else 'phase' if polar else 'imag'
            plot_samples(axes[1], x[valid] if discrete else x, second[valid] if discrete else second,
                         discrete=discrete, label=source.name, source=source, component=kind,
                         phase=kind == 'phase')
        elif polar:
            message = 'Densidad nula: dB = −∞' if density else 'Fase indefinida para módulo cero'
            axes[1].text(.5, .5, message, ha='center', transform=axes[1].transAxes)
        if has_delay:
            draw_delay(axes[2], x, shown, source)
        if terms:
            plot_impulse_areas(axes[-1], terms, source.name)
            axes[-1].set_title('Impulsos ideales', fontsize=9)
    if reduced:
        axes[0].set_title('Vista reducida · Valores contiene todas las muestras', fontsize=9)
    elif any(impulses):
        axes[0].set_title('Parte ordinaria de la señal', fontsize=9)
    if all(source.metadata.get('operation') == 'DFT' for source in signals):
        from .fourier_phase import dft_reference

        references = {dft_reference(source) for source in signals}
        phase_title = ('Referencia de fase no disponible' if None in references else
                       'Fase según los índices n' if references == {'sample_indices'} else
                       'Fase desde la primera muestra (m=0)' if references == {'record_offset'} else
                       'Las trazas tienen referencias de fase distintas')
        existing = axes[0].get_title()
        axes[0].set_title(f'{phase_title}\n{existing}' if existing else phase_title, fontsize=9)
    axes[0].set_ylabel('Densidad' if polar and density else 'Módulo' if polar else 'Parte real')
    axes[1].set_ylabel('Densidad (dB)' if polar and density else 'Fase (rad)' if polar else 'Parte imaginaria')
    configure_signal_axis(axes[-1], signals[0])
    for axis in axes:
        axis.grid(alpha=.2)
        if axis.get_legend_handles_labels()[0]:
            axis.legend()
    if polar:
        note = '10 log10 de la densidad · cero → −∞' if density else 'Fase principal · indefinida para módulo cero'
        axes[1].set_title(note, fontsize=9)


def draw_delay(axis, x, shown, source):
    delay = np.full(source.values.size, np.nan)
    nonzero = np.flatnonzero(np.abs(source.values) > 0)
    for segment in np.split(nonzero, np.flatnonzero(np.diff(nonzero) > 1) + 1):
        if segment.size > 2:
            phase = np.unwrap(np.angle(source.values[segment]))
            delay[segment[1:-1]] = -np.gradient(phase, source.step)[1:-1]
    line = axis.plot(x, delay[shown], label=source.name)[0]
    line._signallab_probe_values = source.origin, source.step, delay
    axis.set_ylabel('Retardo aprox. (muestras)' if source.units == 'rad/muestra' else 'Retardo aprox. (s)')
    axis.set_title('Derivada numérica de fase · indefinida en ceros o discontinuidades', fontsize=8)


def draw_fraction(axis, signals):
    for source in signals:
        if source.metadata.get('bins'):
            low, high = source.metadata['bounds']
            artists = axis.step(np.r_[low, source.axis, high], np.r_[0., source.values.real, 1.],
                                where='post', label=source.name)
        else:
            artists = axis.plot(source.axis, source.values.real, linestyle='none', marker='.', label=source.name)
        attach_signal(artists, source, 'real')
        configure_signal_axis(axis, source)
        if source.units in ('k', 'bin k'):
            configure_axis(axis, discrete_index=True, units=source.units, label='Índice k', index_symbol='k')
    axis.set_ylabel('Fracción acumulada')
    axis.set_ylim(-.02, 1.02)
    axis.grid(alpha=.15)
