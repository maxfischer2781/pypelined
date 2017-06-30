++++++++++++++++++++++++++++++++++++++++++++++++++
pypelined - stream and pipeline processing service
++++++++++++++++++++++++++++++++++++++++++++++++++

.. image:: https://readthedocs.org/projects/pypelined/badge/?version=latest
    :target: http://pypelined.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://img.shields.io/github/issues-raw/maxfischer2781/pypelined.svg
   :target: https://github.com/maxfischer2781/pypelined/issues
   :alt: Open Issues

Service and framework for creating and running processing pipelines for data streams, events and chunks.
Pipelines of ``pypelined`` are composed from individual elements using the chainlet_ library.
They are built in Python configuration files, from custom objects or pre-defined plugins.

.. code:: python

    import chainlet
    from pypelined.conf import pipelines

    @chainlet.funclet
    def add_time(chunk):
        chunk['tme'] = time.time()
        return chunk

    process_chain = Socket(10331) >> decode_json() >> stop_if(lambda value: value.get('rcode') == 0) >> \
        add_time() >> Telegraf(address=('localhost', 10332), name='chunky')
    pipelines.append(process_chain)

Once running, ``pypelined`` drives all its processing pipelines in an event driven fashion.

.. _chainlet: http://chainlet.readthedocs.io/en/stable/
