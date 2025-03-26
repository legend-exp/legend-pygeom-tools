pyg4ometry API extensions
=========================

Detector registration
---------------------

.. py:class:: pyg4ometry.geant4.PhysicalVolume

    .. py:method:: set_pygeom_active_detector(det_info)

       :param det_info:
       :type det_info: RemageDetectorInfo | None

       Set the remage detector info on this physical volume instance.

    .. py:method:: get_pygeom_active_detector()

       :rtype: RemageDetectorInfo | None

       Get the remage detector info on this physical volume instance.

       .. important::
           this only returns instances previously set via :meth:`set_pygeom_active_detector` or
           :attr:`pygeom_active_detector`, not data loaded from GDML.

    .. py:attribute:: pygeom_active_detector

        :type: RemageDetectorInfo | None
        :deprecated: use :meth:`set_pygeom_active_detector`/:meth:`get_pygeom_active_detector` instead

        get or set the active detector instance.


Visualization
-------------

.. py:class:: pyg4ometry.geant4.LogicalVolume

    .. py:attribute:: pygeom_color_rgba

        :type: False | tuple[float, float, float, float]
        :value: (initially not set)

        ``False`` (hidden) or a RGBA color tuple (range 0-1)

        .. warning::

            will raise an :class:`AttributeError` if trying to access without setting first.
