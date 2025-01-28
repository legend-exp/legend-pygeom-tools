Welcome to legendtools's documentation!
==========================================

For geometry writers
--------------------

If your geometry creation script/notebook/application is already set up correctly, you
can use the following set of attributes to control the package's output.

Registering detectors for use with `remage`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On a physical volume instance, you can attach a ``pygeom_active_detector``, e.g.

.. code:: python

   from pygeomtools import RemageDetectorInfo

   pv = g4.PhysicalVolume(...)

   # attach an active detector to this physical volume.
   pv.pygeom_active_detector = RemageDetectorInfo(
       "optical",  # detector type. The available options are defined by remage.
       1,  # detector id in remage.
       {"some": "metadata"},  # user-defined data (optional) that is stored into GDML.
   )


Adjusting the visualization
^^^^^^^^^^^^^^^^^^^^^^^^^^^

On a logical volume instance, you can set ``pygeom_color_rgba``, e.g.

.. code:: python

   lv = g4.LogicalVolume(...)

   # hide this volume in the visualization
   lv.pygeom_color_rgba = False

   # set the vis coloring to the given RGBA value. All 4 numbers should be given in the range 0–1.
   lv.pygeom_color_rgba = (r, g, b, a)

For application developers (general setup)
------------------------------------------

.. code:: python

    from pygeomtools import detectors, geometry, visualization

    reg = geant4.Registry()

    # your geometry building
    # include some of the things described above (detectors, coloring)
    # ...

    detectors.write_detector_auxvals(reg)
    visualization.write_color_auxvals(reg)
    geometry.check_registry_sanity(reg, reg)

    # now write out the GDML or visualize it.


Table of Contents
-----------------

.. toctree::
   :maxdepth: 1

   Metadata in GDML <metadata>
   GDML viewer <vis>
   Package API reference <api/modules>

.. _remage: https://github.com/legend-exp/remage
