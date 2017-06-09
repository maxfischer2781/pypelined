from __future__ import absolute_import
import os
import logging
import argparse

from . import __about__
from .conf import loader, logger
from . import driver

_LOGGER = logging.getLogger(__name__)


def env_key(cli_key):
    _key = cli_key.strip('-')
    _key = __about__.__title__ + '-' + _key
    _key = _key.replace('-', '_')
    return _key.upper()


CLI = argparse.ArgumentParser(__about__.__title__)
CLI_CONFIG = CLI.add_argument_group('configuration options')
CLI_CONFIG.add_argument(
    'configuration',
    metavar='CONFIGURATION',
    nargs='*',
    default=['/etc/%s/*.py' % __about__.__title__],
    help='configuration file paths or globs [%(default)s]',
)
CLI_LOGGING = CLI.add_argument_group('logging options')
CLI_LOGGING.add_argument(
    '-l', '--log-level',
    metavar='LEVEL',
    default=os.environ.get(env_key('log-level'), 'WARNING'),
    help='logging verbosity, numeric or name [%%(default)s] ($%s)' % env_key('log-level'),
)
CLI_LOGGING.add_argument(
    '-f', '--log-format',
    metavar='FORMAT',
    help='logging message format [%%(default)s] ($%s)' % env_key('log-format'),
    default=os.environ.get(env_key('log-format'), '%(asctime)s (%(process)d) %(levelname)8s: %(message)s'),
)
CLI_LOGGING.add_argument(
    '-d', '--log-dest',
    metavar='DEST',
    help='logging destinations, as file path or stderr/stdout [%%(default)s] ($%s)' % env_key('log-dest'),
    nargs='*',
    default=[elem.strip() for elem in os.environ.get(env_key('log-dest'), 'stderr').split(',')]
)

options = CLI.parse_args()

_LOGGER.warning('## %s [v%s] %s' % (
    __about__.__title__, __about__.__version__, __about__.__url__)
)
logger.configure_logging(log_level=options.log_level, log_format=options.log_format, log_dest=options.log_dest)
for opt_name in ('configuration', 'log_level', 'log_dest', 'log_format'):
    _LOGGER.info('%-16s => %r', opt_name, getattr(options, opt_name))
pipelines = loader.run_configurations(options.configuration)
pipeline_driver = driver.PipelineDriver()
for pipeline in pipelines:
    pipeline_driver.mount(pipeline)
pipeline_driver.run()
