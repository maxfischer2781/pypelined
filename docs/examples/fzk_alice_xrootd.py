from chainlet.protolink import filterlet

from pypelined.conf import pipelines
from pypelined.provider.xrootd import xrdreports
from pypelined.modifier.dictlets import update, remap
from pypelined.consumer.alice_apmon import alice_xrootd
from pypelined.consumer.telegraf import telegraf_message
from pypelined.consumer.socket import udp_send

xrd_report_port = 20333
telegraf_port = 20332

# ALICE monitoring backend
alice_backend = alice_xrootd('localhost:8560')

# Telegraf monitoring backend
# translate report keys to more descriptive names
telegraf_remap = remap({
    'pgm': 'daemon', 'info.host': 'hostname', 'ins': 'instance', 'ver': 'version', 'ofs.role': 'role',
    'site': 'se_name', 'oss.space.0.tot': 'space_total', 'oss.space.0.free': 'space_free',
    'link.num': 'connections', 'ofs.han': 'filehandles', 'sched.threads': 'threads',
    'link.in': 'bytes_recv', 'link.out': 'bytes_sent'
})
telegraf_backend =\
    filterlet(lambda report: 'pgm' in report) >> telegraf_remap >>\
    telegraf_message(name='xrootd_reports', dynamic_tags=('hostname', 'daemon', 'instance', 'role', 'se_name')) >>\
    udp_send('localhost', telegraf_port)

# push xrootd reports to ALICE and Telegraf
pipelines.append(xrdreports(xrd_report_port) >> update(site='ALICE::TEST::SE') >> (alice_backend, telegraf_backend))
