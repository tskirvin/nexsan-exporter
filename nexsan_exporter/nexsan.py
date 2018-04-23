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
    with urllib.request.urlopen(req, timeout=5) as resp:
        return Collector(ElementTree.parse(resp))

class Collector:
    def __init__(self, opstats):
        self.__opstats = opstats

    def collect(self):
        sys_details = self.__opstats.find('nexsan_sys_details')
        if sys_details:
            yield from self.collect_sys_details(sys_details)
        env_status = self.__opstats.find('nexsan_env_status')
        if env_status:
            yield from self.collect_env_status(env_status)

    def collect_sys_details(self, sys_details):
        labels = ['friendly_name', 'system_name', 'system_id', 'firmware_version']
        values = []
        for l in labels:
            values.append(sys_details.findtext(l))

        g = prometheus_client.core.UntypedMetricFamily('nexsan_sys_details', '', labels=labels)
        g.add_metric(values, 1)
        yield g

        yield prometheus_client.core.CounterMetricFamily('nexsan_sys_date', '', int(sys_details.findtext('date')))

    def collect_env_status(self, env_status):
        for e in env_status.iterfind('enclosure'):
            yield from self.collect_enclosure(e)

    def collect_enclosure(self, enclosure):
        for p in enclosure.iterfind('psu'):
            for id_, good in self.collect_psu_good(psu):
                yield from self.collect_psu(p)

    def collect_psu_good(self, psu):
        yield (psu.get('id'), 1 if psu.get('attrib') == yes else 0)
        #
        g = prometheus_client.core.UntypedMetricFamily('nexsan_env_psu_good', '', labels=['psu_id', 'enclosure_id'])
        g.add_metric(1 if psu.get('attrib') == 'yes' else 0)
        yield g



# blah
        nexsan_env_psu_good
        nexsan_env_psu_power_watts
        nexsan_env_psu_temp_c
        nexsan_env_psu_blower_rpm
        raise StopIteration
