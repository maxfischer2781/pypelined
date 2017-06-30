import socket
import os
import sys
import hashlib
import filelock
import glob
import time
import threading
import logging
import weakref
import operator
import random
import errno

from .singleton import Singleton


#: Identifier for the process owning a counter
OWNER_IDENTIFIER = '%s\t%s\t%s' % (socket.getfqdn(), os.getpid(), sys.executable)


# actually a method of DFSCounter
# must be separate to allow garbage collection of self
def _count_updater(self):
    """separate counter loop to regularly check/verify state"""
    assert isinstance(self, weakref.ProxyTypes), "counter thread must receive weakref'd self to be collectible"
    # locally rebind everything we need to work
    self_repr = self.__repr__().replace('value=None', 'value=?')
    marker_path = self._marker_path
    thread_shutdown = self._thread_shutdown
    host_lock = self._host_lock
    logger = self._logger
    self._logger.info('acquiring %r @ %r', self_repr, marker_path)
    with host_lock:
        while not thread_shutdown.is_set():
            try:
                with open(marker_path, 'w') as marker:
                    marker.write(OWNER_IDENTIFIER)
                    logger.debug('marking %r @ %r', self_repr, marker_path)
                self._count_value = self._get_count()
            except ReferenceError:
                pass
            except Exception as err:
                logger.warning('failed updating %r: %s', self_repr, err)
            # wait for a fraction of timeout to allow write failures
            # jitter wait to smooth out path access
            thread_shutdown.wait(self.timeout / (3 + random.random()))
        logger.info('releasing %r @ %r', self_repr, marker_path)
        if os.path.exists(marker_path) and os.path.isfile(marker_path):
            os.unlink(marker_path)


class DFSCounter(Singleton):
    """
    Counter for hosts accessing the same Distributed File System

    :param shared_path: path used for synchronisation
    :type shared_path: str
    :param timeout: maximum age of synchronisation in seconds before assuming stale processes
    :type timeout: int or float

    This class pretends to be an integer for all operators. It counts the number
    of processes accessing the `shared_path`, and directly represents the result.
    Only one process per host may claim the `shared_path` at any time.
    """
    def __init__(self, shared_path, timeout=300):
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._thread_shutdown = threading.Event()
        self._thread_shutdown.clear()
        if not os.path.exists(os.path.dirname(shared_path)):
            raise OSError(errno.ENOENT, 'no such directory: %s' % os.path.dirname(shared_path))
        self.shared_path = shared_path
        self.timeout = timeout
        self._host_identifier = socket.getfqdn()
        self._marker_path = self._get_marker_path(hashlib.sha1(self._host_identifier.encode()).hexdigest())
        self._host_lock = filelock.FileLock(self._marker_path + '.lock')
        self._count_value = None
        self._thread = threading.Thread(target=_count_updater, args=(weakref.proxy(self),))
        self._thread.start()
        self._acquire()

    @classmethod
    def __singleton_signature__(cls, shared_path, timeout=300):
        return DFSCounter, shared_path

    def _acquire(self):
        # block until we own the resource
        block_delay = 0.005
        # we need to both OWN the resource (lock) and GET it as well (counter)
        while not self._host_lock.is_locked or self._count_value is None:
            self._logger.debug('waiting for exclusive host lock @ %r', self._marker_path)
            time.sleep(block_delay)
            block_delay = min(block_delay * 2, 5)
        self._logger.debug('acquired %r', self)

    def _get_marker_path(self, identifier):
        return '%s.dfsc-%s.csv' % (self.shared_path, identifier)

    # cross host counting
    def _get_count(self):
        min_age = time.time() - self.timeout
        return sum(1 for file_path in glob.iglob(self._get_marker_path('*')) if os.stat(file_path).st_mtime > min_age)

    def release(self):
        """Release the underlying resource"""
        self._thread_shutdown.set()

    def __del__(self):
        self._thread_shutdown.set()

    # representation
    def __str__(self):
        return str(int(self))

    def __repr__(self):
        return '<%s(shared_path=%r, timeout=%s), value=%s>' % (
            type(self).__name__, self.shared_path, self.timeout, self._count_value
        )

    # overriding __class__ at the instance level does not work, but changing the slot wrapper does
    @property
    def __class__(self):
        return int

    # comparisons
    def __lt__(self, other):
        return int(self) < other

    def __le__(self, other):
        return int(self) <= other

    def __eq__(self, other):
        return int(self) == other

    def __ne__(self, other):
        return int(self) != other

    def __gt__(self, other):
        return int(self) > other

    def __ge__(self, other):
        return int(self) >= other

    # value may change, not hashable
    __hash__ = None

    # number interface
    def __int__(self):
        return self._count_value

    __index__ = __int__

    def __complex__(self):
        return complex(int(self))

    def __float__(self):
        return float(int(self))

    def __long__(self):
        return long(int(self))

    def __round__(self, ndigits):
        return round(int(self), ndigits=ndigits)

    def __bytes__(self):
        return bytes(int(self))

    def __oct__(self):
        return oct(int(self))

    def __hex__(self):
        return hex(int(self))

    def __neg__(self):
        return -int(self)

    def __pos__(self):
        return int(self)

    def __abs__(self):
        return abs(int(self))

    def __invert__(self):
        return ~int(self)

    def __add__(self, other):
        return int(self) + other

    def __radd__(self, other):
        return other + int(self)

    def __sub__(self, other):
        return int(self) - other

    def __rsub__(self, other):
        return other - int(self)

    def __mul__(self, other):
        return int(self) * other

    def __rmul__(self, other):
        return other * int(self)

    def __floordiv__(self, other):
        return int(self) // other

    def __rfloordiv__(self, other):
        return other // int(self)

    def __mod__(self, other):
        return int(self) % other

    def __rmod__(self, other):
        return other % int(self)

    def __divmod__(self, other):
        return divmod(int(self), other)

    def __rdivmod__(self, other):
        return divmod(other, int(self))

    def __pow__(self, other, modulo):
        return pow(int(self), other, modulo)

    def __rpow__(self, other):
        return other ** int(self)

    def __lshift__(self, other):
        return int(self) << other

    def __rlshift__(self, other):
        return other << int(self)

    def __rshift__(self, other):
        return int(self) >> other

    def __rrshift__(self, other):
        return other >> int(self)

    def __and__(self, other):
        return int(self) & other

    def __rand__(self, other):
        return other & int(self)

    def __xor__(self, other):
        return int(self) ^ other

    def __rxor__(self, other):
        return other ^ int(self)

    def __or__(self, other):
        return int(self) | other

    def __ror__(self, other):
        return other | int(self)

    def __div__(self, other):
        return operator.div(int(self), other)

    def __rdiv__(self, other):
        return operator.div(other, int(self))

    def __truediv__(self, other):
        return operator.truediv(int(self), other)

    def __rtruediv__(self, other):
        return operator.truediv(other, int(self))
