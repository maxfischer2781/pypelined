from __future__ import absolute_import
import os
import sys
import logging.handlers


def configure_logging(log_level, log_format, log_dest):
    """
    Configure logging from CLI options

    :param log_level: logging verbosity
    :type log_level: int or str
    :param log_format: format string for messages
    :type log_format: str
    :param log_dest: where to send log message to
    :type log_dest: tuple[str]

    Each element in `destinations` must be either a stream name
    (`"stdout"` or `"stderr"`), or it is interpreted as a file name.
    """
    try:
        log_level = getattr(logging, log_level.upper())
    except AttributeError:
        pass
    log_level = int(log_level)
    root_handlers = logging.getLogger().handlers[:]
    logging.basicConfig(format=log_format, level=log_level)
    root_fmt = logging.getLogger().handlers[0].formatter
    # we add handlers by ourselves to use appropriate classes
    # during initialisation, use the default handler in case something goes wrong
    for destination in log_dest:
        if destination == 'stderr':
            root_handlers.append(logging.StreamHandler(sys.stderr))
        elif destination == 'stdout':
            root_handlers.append(logging.StreamHandler(sys.stdout))
        else:
            if not os.path.isdir(os.path.dirname(destination)):
                os.makedirs(os.path.dirname(destination))
            root_handlers.append(logging.handlers.WatchedFileHandler(filename=destination))
        root_handlers[-1].setFormatter(root_fmt)
    logging.getLogger().handlers[:] = root_handlers
