from __future__ import annotations

import pytest
from pyg4ometry import geant4 as g4

from pygeomtools.materials import BaseMaterialRegistry, cached_property


class DummyMaterials:
    @cached_property
    def x(self) -> str:
        return {"test"}


def test_cached_property():
    m = DummyMaterials()

    first_prop_access = m.x
    assert first_prop_access == {"test"}

    assert m.x == {"test"}
    assert m.x is not {"test"}  # noqa: F632 (just a sanity check)
    assert first_prop_access is m.x  # we should get back the same object.

    # writing and deleting is not possible.
    with pytest.raises(AttributeError):
        m.x = None
    with pytest.raises(AttributeError):
        del m.x


class DummyMaterialRegistry(BaseMaterialRegistry):
    pass


def test_material_registry():
    registry = g4.Registry()
    mat = DummyMaterialRegistry(registry)

    assert registry.materialDict == {}

    ar = mat.get_element("Ar")
    assert ar.Z == 18
    assert ar.registry is registry
    assert registry.materialDict == {"argon": ar}

    # the second access should return the same object and should not raise an error.
    ar2 = mat.get_element("Ar")
    assert ar is ar2
