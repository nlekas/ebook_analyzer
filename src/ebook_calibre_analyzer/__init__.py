"""
Ebook-Calibre Library Analyzer

A Python package to analyze ebook files in a datalake and compare them against
a Calibre library to identify files that exist in the datalake but are not yet
in the Calibre library.
"""

try:
    from ._version import version as __version__
except ImportError:
    # Fallback if setuptools-scm hasn't generated _version.py yet
    __version__ = "0.1.0"
