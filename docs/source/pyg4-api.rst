pyg4ometry API extensions
=========================

Detector registration
---------------------

.. py:class:: pyg4ometry.geant4.PhysicalVolume

    .. py:method:: set_pygeom_active_detector(det_info)

       :param det_info:
       :type det_info: RemageDetectorInfo

       Set the remage detector info on this physical volume instance.

    .. py:method:: get_pygeom_active_detector()

       :rtype: RemageDetectorInfo | None

       Get the remage detector info on this physical volume instance.

    .. py:attribute:: pygeom_active_detector

        :type: RemageDetectorInfo
        :value: (initially not set)
        :deprecated: use :meth:`set_pygeom_active_detector`/:meth:`get_pygeom_active_detector` instead

        get or set the active detector instance.

        .. warning::

            will raise an :class:`AttributeError` if trying to access without setting first.

Visualization
-------------

.. py:class:: pyg4ometry.geant4.LogicalVolume

    .. py:attribute:: pygeom_color_rgba

        :type: False | tuple[float, float, float, float]
        :value: (initially not set)

        ``False`` (hidden) or a RGBA color tuple (range 0-1)

        .. warning::

            will raise an :class:`AttributeError` if trying to access without setting first.
