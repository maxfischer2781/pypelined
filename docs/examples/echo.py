import sys

import chainlet.protolink

from pypelined.conf import pipelines
from pypelined.provider.stream import readlines


@chainlet.genlet()
def reformat():
    chunk = yield
    while True:
        chunk = yield chunk.upper() + '!!!'

pipelines.append(readlines(sys.stdin) >> reformat() >> chainlet.protolink.printlet())
