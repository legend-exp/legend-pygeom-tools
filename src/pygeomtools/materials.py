"""Subpackage to provide a baseline for implementing materials in geometries.

Usage of this module's contents is optional for geometry development with
*legend-pygeom-tools*, it is completely equivalent to manual construction and
registration of materials.
"""

from __future__ import annotations

from abc import ABC
from functools import wraps
from typing import Callable

import pyg4ometry.geant4 as g4


def cached_property(material: Callable):
    @wraps(material)
    def wrapper(self):
        attr = f"_{material.__name__}"
        if not hasattr(self, attr):
            setattr(self, attr, material(self))
        return getattr(self, attr)

    return property(wrapper)


class BaseMaterialRegistry(ABC):  # noqa: B024
    def __init__(self, g4_registry: g4.Registry):
        self.g4_registry = g4_registry

        self._elements = {}
        self._elements_cb = {}
        self._define_elements()

    def get_element(self, symbol: str) -> g4.Element:
        if (symbol in self._elements_cb) and (symbol not in self._elements):
            self._elements[symbol] = (self._elements_cb[symbol])()
        return self._elements[symbol]

    def _add_element(self, name: str, symbol: str, z: int, a: float) -> None:
        """Lazily define an element on the current registry."""
        assert symbol not in self._elements_cb
        self._elements_cb[symbol] = lambda: g4.ElementSimple(
            name=name, symbol=symbol, Z=z, A=a, registry=self.g4_registry
        )

    def _define_elements(self) -> None:
        """Lazily define all used elements."""
        self._add_element(name="Hydrogen", symbol="H", z=1, a=1.00794)
        self._add_element(name="Boron", symbol="B", z=5, a=10.811)
        self._add_element(name="Carbon", symbol="C", z=6, a=12.011)
        self._add_element(name="Nitrogen", symbol="N", z=7, a=14.01)
        self._add_element(name="Oxygen", symbol="O", z=8, a=16.00)
        self._add_element(name="Fluorine", symbol="F", z=9, a=19.00)
        self._add_element(name="Sodium", symbol="Na", z=11, a=22.99)
        self._add_element(name="Aluminium", symbol="Al", z=13, a=26.981539)
        self._add_element(name="Silicon", symbol="Si", z=14, a=28.09)
        self._add_element(name="argon", symbol="Ar", z=18, a=39.95)
        self._add_element(name="Chromium", symbol="Cr", z=24, a=51.9961)
        self._add_element(name="Manganese", symbol="Mn", z=25, a=54.93805)
        self._add_element(name="Iron", symbol="Fe", z=26, a=55.845)
        self._add_element(name="Indium", symbol="In", z=49, a=114.82)
        self._add_element(name="Cobalt", symbol="Co", z=27, a=58.9332)
        self._add_element(name="Nickel", symbol="Ni", z=28, a=58.6934)
        self._add_element(name="Copper", symbol="Cu", z=29, a=63.55)
        self._add_element(name="Tantalum", symbol="Ta", z=73, a=180.94)
        self._add_element(name="Gold", symbol="Au", z=79, a=196.967)
