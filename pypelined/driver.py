from __future__ import division, absolute_import
import logging

import chainlet.driver


class PipelineDriver(chainlet.driver.ThreadedChainDriver):
    """
    Driver for processing pipelines
    """
    def __init__(self):
        super(PipelineDriver, self).__init__()
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))

    def run(self):
        """
        Collect and pass on reports
        """
        self._logger.info('driving %d pipeline(s)', len(self.mounts))
        self._logger.info('starting %s main loop', self.__class__.__name__)
        super(PipelineDriver, self).run()
        self._logger.info('stopping %s main loop', self.__class__.__name__)
