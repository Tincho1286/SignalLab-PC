"""Versioned scientific metadata. Project owns relationships between records."""

from dataclasses import asdict


def scientific_metadata(operation, parameters, *, version=1):
    return {'schema': version, 'operation': operation, **asdict(parameters)}
