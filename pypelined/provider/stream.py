from __future__ import absolute_import
import os
import errno
import time

import chainlet


@chainlet.genlet(prime=False)
def readlines(filelike):
    """
    Read lines from a file-like object

    Stops once the underlying object no longer provides any lines.
    """
    for line in filelike:
        yield line[:-1]


@chainlet.genlet(prime=False)
def tail_path(path, follow=True, **open_kwargs):
    """
    Stream data from a file, socket or similar object at ``path``

    Reads and provides lines of data from ``path`` (excluding line breaks).
    This works similar to the ``tail -F`` unix utility.

    :param path: the file system location suitable for :py:func:`open`
    :type path: str
    :param follow: whether to proceed reading from a new file if the original one is replaced
    :type follow: bool
    :param open_kwargs: keyword arguments to pass to :py:func:`open`

    Note that ``follow`` does not require immediate replacement with a *new* file.
    In ``follow`` mode, any errors from ``path`` not existing are ignored.
    Without ``follow`` mode, it is an error if ``path`` does not exist when the first chunk is fetched.
    Any other errors from :py:func:`open` are propagated unconditionally.
    """
    if follow:
        eof_delay = 0.01
        while True:
            try:
                for chunk in _tail_path_once(path, **open_kwargs):
                    yield chunk
            except OSError as err:
                if err.errno != errno.ENOENT:
                    raise
                time.sleep(eof_delay)
                eof_delay = min(0.5, eof_delay * 2)
            else:
                # if the file has been properly closed, reset delay
                eof_delay = 0.01
    else:
        for chunk in _tail_path_once(path, **open_kwargs):
            yield chunk


def _tail_path_once(path, **open_kwargs):
    eof_delay = 0.01
    path_inode = os.stat(path).st_ino
    with open(path, **open_kwargs) as stream:
        while True:
            line = stream.readline()
            if not line:
                # File is at EOF
                # - the target has been deleted or rotated
                if not os.path.exists(path) or os.stat(path).st_ino != path_inode:
                    break
                # - the file is still valid, smoothly delay further reads
                else:
                    time.sleep(eof_delay)
                    eof_delay = min(0.5, eof_delay * 2)
            else:
                eof_delay = 0.01
                yield line[:-1]  # strip away linebreak
