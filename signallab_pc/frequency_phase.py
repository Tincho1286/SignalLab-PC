"""Phase conventions for rational and general frequency responses."""
import numpy as np

from .jobs import checkpoint


def principal_phase(response):
    valid = np.isfinite(response) & (response != 0)
    return np.where(valid, np.angle(response), np.nan)


def rational_phase(system, omega, response, advance=0):
    """Unwrap the factors analytically, then check their argument against H."""
    from .transfer_plane import plane_roots

    principal = principal_phase(response)
    valid = np.isfinite(principal)
    if not np.any(valid):
        return principal, 'principal'
    digital = system.domain == 'digital'
    if digital and system.sos is None and len(system.a) == 1:
        nonzero = np.flatnonzero(system.b)
        if len(nonzero) == 1:
            trend = (advance+system.advance-int(nonzero[0]))*omega
            return _anchor(principal, trend, valid)
        if np.all(system.b.imag == 0) and (np.array_equal(system.b, system.b[::-1]) or np.array_equal(system.b, -system.b[::-1])):
            trend = (advance+system.advance-(len(system.b)-1)/2)*omega
            phase = trend + np.angle(np.exp(1j*(principal-trend)))
            return phase, 'continuous'
    # Dense companion roots are cubic in the order and increasingly ill-conditioned.
    # Large polynomials retain a labeled principal angle unless their phase is known.
    if system.sos is None and max(len(system.a), len(system.b)) > 129:
        return principal, 'principal'
    try:
        zeros, poles = plane_roots(system)
    except (ValueError, FloatingPointError, np.linalg.LinAlgError, MemoryError):
        return principal, 'principal'
    if not np.isfinite(zeros).all() or not np.isfinite(poles).all():
        return principal, 'principal'

    if system.domain == 'digital':
        unit = np.exp(1j*omega)
        curve = omega * float(advance)

        def argument(root):
            if abs(root) <= 1:
                return omega + np.angle(1-root*unit.conj())
            return np.angle(-root) + np.angle(1-unit/root)
    else:
        curve = np.zeros_like(omega)

        def argument(root):
            offset = -root.real
            height = omega-root.imag
            if offset < 0:
                return np.pi + np.arctan2(-height, -offset)
            return np.arctan2(height, offset)

    for sign, roots in ((1, zeros), (-1, poles)):
        origin = roots == 0
        if system.domain == 'digital':
            curve += sign * np.count_nonzero(origin) * omega
            roots = roots[~origin]
        for root in roots:
            checkpoint()
            curve += sign * argument(root)

    return _anchor(principal, curve, valid)


def _anchor(principal, curve, valid):
    indices = np.flatnonzero(valid)
    phase = principal.copy()
    for segment in np.split(indices, np.flatnonzero(np.diff(indices)>1)+1):
        anchor = segment[0]
        expected = principal[anchor] + (curve[segment]-curve[anchor])
        residue = np.angle(np.exp(1j*(principal[segment]-expected)))
        if not np.isfinite(residue).all() or np.any(abs(residue)>1e-6):
            return principal, 'principal'
        phase[segment] = expected+residue
    return phase, 'continuous'
