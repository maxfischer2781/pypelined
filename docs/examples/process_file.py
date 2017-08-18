from chainlet.protolink import enumeratelet, printlet

import os
import shutil
import threading

from pypelined.conf import pipelines
from pypelined.provider.stream import tail_path

# short-lived temporary file to stream to and from
temp_path = __file__ + '.tmp'
shutil.copy(__file__, temp_path)
threading.Timer(2, lambda: open(temp_path, 'a').write('# The End!\n')).start()
threading.Timer(3, lambda: os.unlink(temp_path)).start()

# pipeline that reads from file and enumerates lines
pipelines.append(
    tail_path(temp_path, follow=False) >> enumeratelet() >> printlet(flatten=True)
)
