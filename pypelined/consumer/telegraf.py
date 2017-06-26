from __future__ import absolute_import, division
import time

import chainlet


def _line_format(name, tags, fields, timestamp=None):
    """
    Format a report as InfluxDB line format

    :param name: name of the report
    :type name: str
    :param tags: tags identifying the specific report
    :type tags: dict[str]
    :param fields: measurements of the report
    :type fields: dict[str]
    :param timestamp: when the measurement was taken, in **seconds** since the epoch
    :type timestamp: float, int or None
    """
    output_str = name
    if tags:
        output_str += ',' + ','.join('%s=%s' % (key, value) for key, value in sorted(tags.items()))
    output_str += ' '
    output_str += ','.join(('%s=%r' % (key, value)).replace("'", '"') for key, value in sorted(fields.items()))
    if timestamp is not None:
        # line protocol requires nanosecond precision, python uses seconds
        output_str += ' %d' % (timestamp * 1E9)
    return output_str + '\n'


@chainlet.genlet
def telegraf_message(name, static_tags=None, dynamic_tags=(), fields=None, time_resolution=1):
    """
    Convert mapping data to line format reports suitable for telegraf

    :param name: name of the measurement
    :type name: str
    :param static_tags: predefined tags to identify the measurement, e.g. ``{'location': 'hawaii'}``
    :type static_tags: dict[str, str]
    :param dynamic_tags: keys to read from each data chunk and add as tags
    :type dynamic_tags: set[str], list[str], tuple[str]
    :param fields: keys of the report to pass on as fields; if :py:const:`None`, pass on all non-tag keys
    :type fields: set[str], list[str], tuple[str] or None
    :param time_resolution: resolution at which timestamps are reported, in seconds
    :type time_resolution: int or float
    """
    static_tags = static_tags or {}
    report = yield
    while True:
        message_tags = static_tags.copy()
        message_fields = {}
        for key in report:
            if key in dynamic_tags:
                message_tags[key] = report[key]
            elif fields is None or key in fields:
                message_fields[key] = report[key]
        message = _line_format(
                name=name % report,
                tags=message_tags,
                fields=message_fields,
                timestamp=(time.time() // time_resolution)*time_resolution
            )
        report = yield message
