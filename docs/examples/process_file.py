"""
This example enumerates a copy of itself line-by-line
"""
import os
import shutil
import threading

from chainlet.protolink import enumeratelet, printlet

from pypelined.conf import pipelines
from pypelined.provider.stream import tail_path
from pypelined.modifier.nooplets import delay

# short-lived temporary file to stream to modify and delete
temp_path = __file__ + '.tmp'
shutil.copy(__file__, temp_path)
threading.Timer(3, lambda: open(temp_path, 'a').write('# The End!\n# Waiting for deletion...\n')).start()
threading.Timer(3.5, lambda: os.unlink(temp_path)).start()

# actual pipeline that reads cloned file and enumerates lines
pipelines.append(
    tail_path(temp_path, follow=False) >> delay(duration=0.1) >> enumeratelet() >> printlet(flatten=True)
)
