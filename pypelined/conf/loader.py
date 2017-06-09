from __future__ import absolute_import
import logging
import glob
import platform

import include

from .. import conf


_LOGGER = logging.getLogger(__name__)


def run_configurations(config_globs, pipelines=None):
    _LOGGER.warning('running configuration')
    _prev_pipelines = conf.pipelines
    conf.pipelines = pipelines = pipelines if pipelines is not None else []
    _LOGGER.info('%-16s => %s %s', 'interpreter', platform.python_implementation(), platform.python_version())
    _LOGGER.info('%-16s => %s', 'globs', config_globs)
    _LOGGER.info('%-16s => <%s> %s', 'pipelines', pipelines.__class__.__name__, pipelines)
    for glob_path in config_globs:
        for config_path in glob.iglob(glob_path):
            _LOGGER.info('configuration: %s', config_path)
            include.path(config_path)
            if conf.pipelines is not pipelines:
                pipelines = conf.pipelines
                _LOGGER.info('%-16s => <%s> %s', 'pipelines', pipelines.__class__.__name__, pipelines)
    conf.pipelines = _prev_pipelines
    return pipelines
