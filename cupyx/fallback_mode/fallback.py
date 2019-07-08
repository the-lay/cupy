"""
Main fallback class.
"""

import types
import numpy as np

import cupy as cp


from cupyx.fallback_mode import utils
from cupyx.fallback_mode import ndarray


class _RecursiveAttr:
    """
    RecursiveAttr class to catch all attributes corresponding to numpy,
    when user calls fallback_mode. numpy is an instance of this class.
    """

    def __init__(self, numpy_object, cupy_object, array=None):

        self._numpy_object = numpy_object
        self._cupy_object = cupy_object
        self._fallback_array = array

    def __instancecheck__(self, instance):
        """
        Enable support for isinstance(instance, _RecursiveAttr instance)
        by redirecting it to appropriate isinstance method.
        Since, we've ndarray wrapper, we need to handle it's __instancecheck__
        separately.
        """
        if self._cupy_object is cp.ndarray:
            return isinstance(instance, ndarray.ndarray)

        if self._cupy_object is not None:
            return isinstance(instance, self._cupy_object)

        return isinstance(instance, self._numpy_object)

    def __getattr__(self, attr):
        """
        Catches attributes corresponding to numpy.

        Runs recursively till attribute gets called.
        Or numpy ScalarType is retrieved.

        Args:
            attr (str): Attribute of _RecursiveAttr class object.

        Returns:
            (_RecursiveAttr object, NumPy scalar):
            Returns_RecursiveAttr object with new numpy_object, cupy_object.
            Returns scalars if requested.
            Returns objects in cupy which is an alias of numpy object.
        """

        # getting attr
        numpy_object = getattr(self._numpy_object, attr)
        cupy_object = getattr(self._cupy_object, attr, None)

        # if same objects, then return
        if numpy_object is cupy_object:
            return numpy_object

        return _RecursiveAttr(numpy_object, cupy_object)

    def __repr__(self):

        if isinstance(self._numpy_object, types.ModuleType):
            return "<numpy = module {}, cupy = module {}>".format(
                self._numpy_object.__name__,
                getattr(self._cupy_object, '__name__', None))

        return "<numpy = {}, cupy = {}>".format(
            self._numpy_object, self._cupy_object)

    @property
    def __doc__(self):
        return self._numpy_object.__doc__

    def __call__(self, *args, **kwargs):
        """
        Gets invoked when last attribute of _RecursiveAttr class gets called.
        Calls _cupy_object if not None else call _numpy_object.

        Args:
            args (tuple): Arguments.
            kwargs (dict): Keyword arguments.

        Returns:
            (res, ndarray): Returns of methods call_cupy or call_numpy
        """

        # Not callable objects
        if not callable(self._numpy_object):
            raise TypeError("'{}' object is not callable".format(
                type(self._numpy_object).__name__))

        # if ndarray method
        if self._fallback_array is not None:
            args = ((self._fallback_array,) + args)

        # Execute cupy method
        if self._cupy_object is not None:
            return utils._call_cupy(self._cupy_object, args, kwargs)

        # Execute numpy method
        return utils._call_numpy(self._numpy_object, args, kwargs)


numpy = _RecursiveAttr(np, cp)
