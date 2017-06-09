from __future__ import absolute_import

import chainlet


@chainlet.genlet(prime=False)
def readlines(filelike):
    for line in filelike:
        yield line[:-1]
