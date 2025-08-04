"""
CRDVis package provides visualization tools for Kubernetes CRD resources.
"""

__version__ = "0.1.0"

from . import models, vis
from .vis import main as run_crdvis

__all__ = ["models", "vis", "run_crdvis"]
