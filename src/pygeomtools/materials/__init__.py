"""Subpackage to provide a baseline for implementing materials in geometries.

Usage of this module's contents is optional for geometry development with
*legend-pygeom-tools*, it is completely equivalent to manual construction and
registration of materials.
"""

from __future__ import annotations

from .base import BaseMaterialRegistry, cached_property
from .legend import LegendMaterialRegistry

__all__ = [
    "BaseMaterialRegistry",
    "LegendMaterialRegistry",
    "cached_property",
]
