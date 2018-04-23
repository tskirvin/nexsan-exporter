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
        self.__parent_map = {c: p for p in opstats.iter() for c in p}

    def isgood(self, elem):
        if elem.attrib['good'] == 'yes':
            return 1
        else:
            return 0

    def collect(self):
        for child in self.__opstats.iterfind('.//*'):
            if child.tag == 'nexsan_sys_details':
                yield from self.collect_sys_details(child)
            elif child.tag == 'nexsan_env_status':
                yield from self.collect_env_status(child)

    def collect_sys_details(self, sys_details):
        labels = ['friendly_name', 'system_name', 'system_id', 'firmware_version']
        g = prometheus_client.core.UntypedMetricFamily('nexsan_sys_details', '', labels=labels)
        g.add_metric([sys_details.findtext(l) for l in labels], 1)
        yield g

        yield prometheus_client.core.CounterMetricFamily('nexsan_sys_date', '', int(sys_details.findtext('date')))

    def collect_env_status(self, env_status):
        for p in env_status.iterfind('.//psu'):
            yield from self.collect_psu(p)

    def collect_psu(self, psu):
        labels = ['psu', 'enclosure']
        values = [psu.attrib['id'], self.__parent_map[psu].attrib['id']]

        g1 = prometheus_client.core.GaugeMetricFamily('nexsan_env_psu_power_good', '', labels=labels)
        g1.add_metric(values, self.isgood(psu.find('state')))
        yield g1

        g2 = prometheus_client.core.GaugeMetricFamily('nexsan_env_psu_power_watts', '', labels=labels)
        g2.add_metric(values, int(psu.find('state').attrib['power_watt']))
        yield g2

        g3 = prometheus_client.core.GaugeMetricFamily('nexsan_env_psu_temp_celsius', '', labels=labels)
        g3.add_metric(values, int(psu.find('temperature_deg_c').text))
        yield g3

        g4 = prometheus_client.core.GaugeMetricFamily('nexsan_env_psu_temp_good', '', labels=labels)
        g4.add_metric(values, self.isgood(psu.find('temperature_deg_c')))
        yield g4
