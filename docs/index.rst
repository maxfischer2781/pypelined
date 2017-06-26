.. pypelined documentation master file, created by
   sphinx-quickstart on Wed Feb 22 14:45:32 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pypelined - stream and pipeline processing service
==================================================

.. image:: https://readthedocs.org/projects/pypelined/badge/?version=latest
    :target: http://pypelined.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. toctree::
    :maxdepth: 1
    :caption: Documentation Topics Overview:

    source/service
    Changelog <source/changelog>
    Module Index <source/api/modules>

The :py:mod:`pypelined` service and framework lets you build and deploy iterative processing pipelines.
Using generator/coroutines with the :py:mod:`chainlet` library, it is trivial to create pipelines to fetch, process and transform streams of data.
Configuration files are written using pure Python, allowing for maximum customization:

.. code:: python

    # this is a pure python configuration file
    from chainlet import funclet, filterlet
    from pypelined.conf import pipelines

    # new pipeline processing element as simple python function
    @funclet
    def add_time(chunk):
        chunk['tme'] = time.time()
        return chunk

    # new pipeline receiving process monitoring reports, modifying them, and sending them to another service
    process_chain = Socket(10331) >> decode_json() >> filterlet(lambda value: value.get('rcode') == 0) >> \
        add_time() >> Telegraf(address=('localhost', 10332), name='valid_processes')
    # add pipeline for deployment
    pipelines.append(process_chain)



.. code:: bash

    python -m pypelined myconfig.py

Contributing and Feedback
-------------------------

The project is hosted on `github <https://github.com/maxfischer2781/pypelined>`_.
If you have issues or suggestion, check the issue tracker: |issues|
For direct contributions, feel free to fork the `development branch <https://github.com/maxfischer2781/pypelined/tree/devel>`_ and open a pull request.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

----------

.. |issues| image:: https://img.shields.io/github/issues-raw/maxfischer2781/pypelined.svg
   :target: https://github.com/maxfischer2781/pypelined/issues
   :alt: Open Issues

Documentation built from chainlet |version| at |today|.
