"""Reusable application adapters for external web targets.

Each adapter owns one site's approved origin, selectors, state
readers, and independent verification. Adapters import nothing from
``chimera``, ``benchmarks``, or ``workbench`` so every layer can use
them without cycles.
"""
