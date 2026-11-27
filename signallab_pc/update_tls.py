"""Use the host trust store even when OpenSSL is bundled with SignalLab."""

import os
from pathlib import Path
import ssl
import sys
from urllib.request import HTTPSHandler


LINUX_CA_BUNDLES = (
    # Fedora installs this canonical bundle even when compatibility links are absent.
    Path('/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem'),
    Path('/etc/pki/tls/certs/ca-bundle.crt'),
    Path('/etc/ssl/certs/ca-certificates.crt'),
    Path('/etc/ssl/cert.pem'),
)


def https_handler():
    bundle = None
    if sys.platform == 'linux' and not any(os.environ.get(name) for name in ('SSL_CERT_FILE', 'SSL_CERT_DIR')):
        bundle = next((path for path in LINUX_CA_BUNDLES if path.is_file()), None)
    return HTTPSHandler(context=ssl.create_default_context(cafile=bundle))


def certificate_error(error):
    return isinstance(getattr(error, 'reason', error), ssl.SSLCertVerificationError)
