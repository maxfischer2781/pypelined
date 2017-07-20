"""
Backend for sending reports using ApMon for the ALICE collaboration
"""
from __future__ import division, absolute_import

import logging
import socket
import time

import apmon
import chainlet

from ..utilities import proctools
from ..utilities import dfs_counter


class ApMonLogger(object):
    """
    Replacement for ApMon `Logger.Logger` class to use default python logging

    :param defaultLevel: ignored, available for signature compatibility only

    Redirects ApMon logging calls messages using the standard :py:mod:`logging`
    utilities. This is intended for compatibility with backend code, mainly
    ApMon itself. If you wish to change ApMon logging settings, directly modify
    the logger `"xrdmonlib.ApMonLogger"`.
    """
    #: log levels as used by ApMon Logger
    apmon_levels = ('FATAL', 'ERROR', 'WARNING', 'INFO', 'NOTICE', 'DEBUG')
    #: map from apmon levels to logging levels
    level_map = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG,
        5: logging.DEBUG,
    }

    def __init__(self, defaultLevel=None):
        self._logger = logging.getLogger('%s.%s' % (__name__.split('.')[0], self.__class__.__name__))
        self._logger.warning('redirecting ApMon logging to native logger %r', self._logger.name)

    def log(self, level, message, printex=False):
        """Log a message from ApMon"""
        self._logger.log(self.level_map[level], '[ApMon] %s', message, exc_info=printex)

    def setLogLevel(self, strLevel):
        """Set the logging level"""
        logging_level = self.level_map[self.apmon_levels.index(strLevel)]
        self._logger.setLevel(logging_level)
        self._logger.log(logging_level, 'logging level set via ApMon: %s => %s', strLevel, logging_level)
for _level, _name in enumerate(ApMonLogger.apmon_levels):
    setattr(ApMonLogger, _name, _level)


class ApMonReport(dict):
    """
    Container for named reports for ApMon following ALICE conventions

    :param cluster_name: identifier for the host group this report applies to
    :type cluster_name: str
    :param node_name: identifier for the host this report applies to
    :type node_name: str
    :param params: parameters to send
    :type params: dict
    """
    def __init__(self, cluster_name, node_name, params):
        super(ApMonReport, self).__init__(self)
        self.cluster_name = cluster_name
        self.node_name = node_name
        self.update(params)


class Reporter(chainlet.ChainLink):
    """
    BaseClass for converters from report dicts to :py:class:`ApMonReport`
    """
    def __init__(self):
        super(Reporter, self).__init__()
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._hostname = socket.getfqdn()

    def _xrootd_cluster_name(self, report):
        """Format report information to create ALICE cluster name"""
        return '%(se_name)s_%(instance)s_%(daemon)s_Services' % {
            'se_name': report['site'],  # must be defined via all.sitename
            'instance': report['ins'],
            'daemon': report['pgm'],
        }


class XrootdSpaceReporter(Reporter):
    """
    Extract XRootD Space information from reports

    :param weight_reporters: weight space statistics by number of reporter hosts
    :type weight_reporters: bool

    Provides key statistics on available space on an xrootd oss:

    *xrootd_version*
        The version of the xrootd daemon

    *space_total*
        The total space in MiB

    *space_free*
        The available space in MiB

    *space_largestfreechunk*
        The largest, consecutive available space in MiB
    """
    def __init__(self, weight_reporters=True):
        super(XrootdSpaceReporter, self).__init__()
        self._space_counters = {}
        self.weight_reporters = weight_reporters

    def chainlet_send(self, value=None):
        if 'oss.paths' not in value:
            raise chainlet.StopTraversal
        xrootd_report = self._oss_path_stats(report=value)
        return ApMonReport(cluster_name=self._xrootd_cluster_name(value), node_name=self._hostname, params=xrootd_report)

    def _oss_path_stats(self, report):
        """Collect statistics from ``oss.path`` fields"""
        try:
            path_count = report['oss.paths']
        except KeyError:
            raise chainlet.StopTraversal
        path_stats = {
            'xrootd_version' : report['ver'],
            'space_total': 0,
            'space_free': 0,
            'space_largestfreechunk': 0,
        }
        for path_id in range(path_count):
            # get real path to volume to count how many reporters see it
            path_rp = report['oss.paths.%d.rp' % path_id]
            path_reporters = self._get_path_share(path_rp)
            self._logger.debug('adding report (%d reporters) for path %r', path_reporters, path_rp)
            # reports are in kiB, MonALISA expects MiB
            path_stats['space_total'] += report['oss.paths.%d.tot' % path_id] / path_reporters / 1024
            path_stats['space_free'] += report['oss.paths.%d.free' % path_id] / path_reporters / 1024
            path_stats['space_largestfreechunk'] = max(
                path_stats['space_largestfreechunk'],
                report['oss.paths.%d.free' % path_id] / 1024
            )
        return path_stats

    def _get_path_share(self, path):
        """Get the number of hosts reporting the same space share"""
        if path not in self._space_counters:
            self._space_counters[path] = dfs_counter.DFSCounter(path)
        return self._space_counters[path]


class AliceApMonBackend(Reporter):
    """
    Backend for ApMon client to MonALISA Monitoring

    :param destination: where to send data to, as `"hostname:port"`
    :type destination: str
    """
    def __init__(self, *destination):
        super(AliceApMonBackend, self).__init__()
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        # initialization
        self.destination = destination
        # initialize ApMon, reroute logging by replacing Logger at module level
        apmon_logger, apmon.Logger = apmon.Logger, ApMonLogger
        self._apmon = apmon.ApMon(destination)
        apmon.Logger = apmon_logger
        # BUGFIX: apmon can create an invalid identifier on systems with pids > 32767
        if any(senderRef['INSTANCE_ID'] > 2147483647 for senderRef in self._apmon.senderRef.values()):
            raise RuntimeError('invalid ApMon INSTANCE_ID')  # https://github.com/MonALISA-CIT/apmon_py/issues/4
        # background monitoring
        self._background_monitor_sitename = None
        self._service_job_monitor = set()

    def chainlet_send(self, value=None):
        """Send reports via ApMon"""
        # preformatted report
        if self._send_apmon_report(value):
            return value
        # regular xrootd report
        self._send_raw_report(value)
        # configure background monitoring of xrootd components from report
        self._monitor_host(value)
        self._monitor_service(value)

    def _send_apmon_report(self, value):
        """Send a report preprocessed for apmon"""
        try:
            cluster_name = value.cluster_name
            node_name = value.node_name
        except AttributeError:
            return False
        else:
            self._apmon.sendParameters(
                clusterName=cluster_name,
                nodeName=node_name,
                params=value
            )
            self._logger.info('apmon report for %r @ %r sent to %s' % (cluster_name, node_name, str(self.destination)))
            return True

    def _send_raw_report(self, value):
        """Send a raw report from xrootd"""
        self._send_apmon_report(ApMonReport(
            cluster_name='%(se_name)s_xrootd_ApMon_Info' % {'se_name': value['site']},
            node_name=self._hostname,
            params=value
        ))

    def _monitor_host(self, value):
        """Add background monitoring for this host"""
        try:
            se_name = value['site']
        except KeyError:
            return False
        if self._background_monitor_sitename == se_name:
            return
        # configure background monitoring
        cluster_name = '%(se_name)s_xrootd_SysInfo' % {'se_name': se_name}
        self._apmon.setMonitorClusterNode(
            cluster_name,
            self._hostname
        )
        self._apmon.enableBgMonitoring(True)
        self._background_monitor_sitename = se_name
        self._logger.info(
            'apmon host monitor for %r @ %r added to %s' % (cluster_name, self._hostname, str(self.destination))
        )
        return True

    def _monitor_service(self, report):
        """Add background monitoring for a service"""
        if 'pgm' not in report or 'pid' not in report:
            return
        pid, now = int(report['pid']), time.time()
        # add new services for monitoring
        if pid not in self._service_job_monitor:
            cluster_name = self._xrootd_cluster_name(report)
            self._apmon.addJobToMonitor(
                pid=pid,
                workDir='',
                clusterName=cluster_name,
                nodeName=self._hostname,
            )
            self._service_job_monitor.add(pid)
            self._logger.info(
                'apmon job monitor for %r @ %r added to %s' % (cluster_name, self._hostname, str(self.destination))
            )
        for pid in list(self._service_job_monitor):
            if not proctools.validate_process(pid):
                self._apmon.removeJobToMonitor(pid)
                self._service_job_monitor.discard(pid)


# full ALICE monitoring backend stack
def alice_xrootd(*destinations):
    """
    Factory for ALICE XRootD ApMon/MonALISA Backend

    :param destinations: where to send data to, as `"hostname:port"`
    :type destinations: str
    """
    backend = AliceApMonBackend(*destinations)
    return (XrootdSpaceReporter(), chainlet.NoOp()) >> backend
