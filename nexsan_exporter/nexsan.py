import base64
import prometheus_client
import traceback
import urllib.request
import urllib.parse

from xml.etree import ElementTree

import prometheus_client

def probe(target, user, pass_):
    '''
    Returns a collector populated with metrics from the target array.
    '''
    auth = b'Basic ' + base64.b64encode('{}:{}'.format(user, pass_).encode('latin1'))
    url = urllib.parse.urlunsplit(('http', target, '/admin/opstats.asp', None, None))
    req = urllib.request.Request(url)
    req.add_header(b'Authorization', auth)

    return Collector(req)

class Collector:
    def __init__(self, req):
        self.__req = req

    def collect(self):
        with urllib.request.urlopen(self.__req, timeout=5) as stats_f:
            stats = ElementTree.parse(stats_f)
            sys_details = stats.find('nexsan_sys_details')
            if sys_details:
                yield from self.collect_sys_details(sys_details)

    def collect_sys_details(self, sys_details):
        labels = ['friendly_name', 'system_name', 'system_id', 'firmware_version', 'date']
        values = []
        for l in labels:
            values.append(sys_details.findtext(label))
        g = prometheus_client.core.GaugeMetricFamily('nexsan_sys_details', labels)
        g.add_metric(values, 1)
