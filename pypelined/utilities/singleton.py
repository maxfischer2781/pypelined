import weakref
import threading


class Singleton(object):
    """
    Basic implementation of a Singleton

    Any instances constructed with the same parameters are actually the same object.
    Use :py:meth:`~.__singleton_signature__` to specify which parameters define identity.
    """
    __singleton_store__ = weakref.WeakValueDictionary()
    __singleton_mutex__ = threading.RLock()

    @classmethod
    def __singleton_signature__(cls, *args, **kwargs):
        # args is always a tuple, but kwargs is mutable and arbitrarily sorted
        return cls, args, tuple(sorted(kwargs.items()))

    def __new__(cls, *args, **kwargs):
        identifier = cls.__singleton_signature__(*args, **kwargs)
        with cls.__singleton_mutex__:
            try:
                self = cls.__singleton_store__[identifier]
            except KeyError:
                self = object.__new__(cls)
                self_init = self.__init__
                self.__singleton_init__ = True

                def singleton_init(*iargs, **ikwargs):
                    """Wrapper to run init only once for each singleton instance"""
                    if self.__singleton_init__:
                        self_init(*iargs, **ikwargs)
                        self.__singleton_init__ = False
                self.__init__ = singleton_init
                self.__init__.__doc__ = self_init.__doc__
                cls.__singleton_store__[identifier] = self
            return self
