+++++++++++++++++++++++++++
pypelined Service Templates
+++++++++++++++++++++++++++

The :py:mod:`pypelined` package is ready for use as a daemon, but does not attempt to provide definitions for every system service.
Depending on the target system, adjustments for deployment into virtual environments and similar are required.

systemd
+++++++

.. code::

    # /etc/systemd/system/pypelined@.service
    [Unit]
    Description=stream and pipeline processing service
    Documentation=https://pypi.python.org/pypi/pypelined

    [Service]
    Type=simple
    Restart=on-failure
    ExecStart=/usr/bin/python -m pypelined /etc/pypelined/%i*.py
    User=daemon
    Nice=-19

    [Install]
    WantedBy=multi-user.target
    DefaultInstance=default
