Welcome to legendtools's documentation!
==========================================

Registering detectors for use with `remage`_
-----------------------------------------------

On a physical volume instance, you can attach a ``pygeom_active_dector``, e.g.

.. code:: python

   from pygeomtools import RemageDetectorInfo

   pv = g4.PhysicalVolume(...)

   # attach an active detector to this physical volume.
   lv.pygeom_active_dector = RemageDetectorInfo(
       "optical",  # detector type. The available options are defined by remage.
       1,  # detector id in remage.
       {"some": "metadata"},  # user-defined data (optional) that is stored into GDML.
   )


Adjusting the visualization
---------------------------

On a logical volume instance, you can set ``pygeom_color_rgba``, e.g.

.. code:: python

   lv = g4.LogicalVolume(...)

   # hide this volume in the visualization
   lv.pygeom_color_rgba = False

   # set the vis coloring to the given RGBA value. All 4 numbers should be given in the range 0–1.
   lv.pygeom_color_rgba = (r, g, b, a)


Table of Contents
-----------------

.. toctree::
   :maxdepth: 1

   Package API reference <api/modules>

.. _remage: https://github.com/legend-exp/remage
