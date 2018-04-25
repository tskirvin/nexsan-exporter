import urllib.request
import urllib.parse

from xml.etree import ElementTree

from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily

def probe(target, user, pass_):
    '''
    Returns a collector populated with metrics from the target array.
    '''
    url = urllib.parse.urlunsplit(('http', target, '/admin/opstats.asp', None, None))

    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, url, user, pass_)
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opener = urllib.request.build_opener(handler)
    with opener.open(url, timeout=5) as resp:
        return Collector(ElementTree.parse(resp))

class Collector:
    def __init__(self, opstats):
        self.__opstats = opstats
        self.__parent_map = {c: p for p in opstats.iter() for c in p}

        self.__nexsan_sys_details = GaugeMetricFamily('nexsan_sys_details', '', labels=['friendly_name', 'system_name', 'system_id', 'firmware_version'])
        self.__nexsan_sys_date = CounterMetricFamily('nexsan_sys_date', '')
        self.__nexsan_env_psu_power_good = GaugeMetricFamily('nexsan_env_psu_power_good', '', labels=['psu', 'enclosure'])
        self.__nexsan_env_psu_power_watts = GaugeMetricFamily('nexsan_env_psu_power_watts', '', labels=['psu', 'enclosure'])
        self.__nexsan_env_psu_temp_celsius = GaugeMetricFamily('nexsan_env_psu_temp_celsius', '', labels=['psu', 'enclosure'])
        self.__nexsan_env_psu_temp_good = GaugeMetricFamily('nexsan_env_psu_temp_good', '', labels=['psu', 'enclosure'])
        self.__nexsan_env_psu_blower_rpm = GaugeMetricFamily('nexsan_env_psu_blower_rpm', '', labels=['psu', 'enclosure', 'blower'])
        self.__nexsan_env_psu_blower_good = GaugeMetricFamily('nexsan_env_psu_blower_good', '', labels=['psu', 'enclosure', 'blower'])
        self.__nexsan_env_controller_voltage_volts = GaugeMetricFamily('nexsan_env_controller_voltage_volts', '', labels=['controller', 'enclosure', 'voltage'])
        self.__nexsan_env_controller_voltage_good = GaugeMetricFamily('nexsan_env_controller_voltage_good', '', labels=['controller', 'enclosure', 'voltage'])
        self.__nexsan_env_controller_temp_celsius = GaugeMetricFamily('nexsan_env_controller_temp_celsius', '', labels=['controller', 'enclosure', 'temp'])
        self.__nexsan_env_controller_temp_good = GaugeMetricFamily('nexsan_env_controller_temp_good', '', labels=['controller', 'enclosure', 'temp'])
        self.__nexsan_env_controller_battery_charge_good = GaugeMetricFamily('nexsan_env_controller_battery_charge_good', '', labels=['controller', 'enclosure', 'battery'])
        self.__nexsan_env_pod_voltage_volts = GaugeMetricFamily('nexsan_env_pod_voltage_volts', '', labels=['pod', 'enclosure', 'voltage'])
        self.__nexsan_env_pod_voltage_good = GaugeMetricFamily('nexsan_env_pod_voltage_good', '', labels=['pod', 'enclosure', 'voltage'])
        self.__nexsan_env_pod_temp_celsius = GaugeMetricFamily('nexsan_env_pod_temp_celsius', '', labels=['pod', 'enclosure', 'temp'])
        self.__nexsan_env_pod_temp_good = GaugeMetricFamily('nexsan_env_pod_temp_good', '', labels=['pod', 'enclosure', 'temp'])
        self.__nexsan_env_pod_front_blower_rpm = GaugeMetricFamily('nexsan_env_pod_front_blower_rpm', '', labels=['pod', 'enclosure', 'blower'])
        self.__nexsan_env_pod_front_blower_good = GaugeMetricFamily('nexsan_env_pod_front_blower_good', '', labels=['pod', 'enclosure', 'blower'])
        self.__nexsan_env_pod_tray_blower_rpm = GaugeMetricFamily('nexsan_env_pod_tray_blower_rpm', '', labels=['pod', 'enclosure', 'blower'])
        self.__nexsan_env_pod_tray_blower_good = GaugeMetricFamily('nexsan_env_pod_tray_blower_good', '', labels=['pod', 'enclosure', 'blower'])
        self.__nexsan_volume_ios_total = CounterMetricFamily('nexsan_volume_ios_total', '', labels=['volume', 'name', 'array', 'serial', 'ident', 'target', 'lun'])
        self.__nexsan_volume_ios_read_total = CounterMetricFamily('nexsan_volume_ios_read_total', '', labels=['volume', 'name', 'array', 'serial', 'ident', 'target', 'lun'])
        self.__nexsan_volume_ios_write_total = CounterMetricFamily('nexsan_volume_ios_write_total', '', labels=['volume', 'name', 'array', 'serial', 'ident', 'target', 'lun'])
        self.__nexsan_volume_blocks_read_total = CounterMetricFamily('nexsan_volume_blocks_read_total', '', labels=['volume', 'name', 'array', 'serial', 'ident', 'target', 'lun'])
        self.__nexsan_volume_blocks_write_total = CounterMetricFamily('nexsan_volume_blocks_write_total', '', labels=['volume', 'name', 'array', 'serial', 'ident', 'target', 'lun'])
        self.__nexsan_perf_cpu_usage_percent = GaugeMetricFamily('nexsan_perf_cpu_usage_percent', '', labels=['controller'])
        self.__nexsan_perf_memory_usage_percent = GaugeMetricFamily('nexsan_perf_memory_usage_percent', '', labels=['controller'])
        for x in ['read_bytes_per_second', 'write_bytes_per_second', 'read_ios_total', 'write_ios_total', 'read_blocks_total', 'write_blocks_total', 'port_resets_total', 'lun_resets_total']:
            c = CounterMetricFamily if x.endswith('_total') else GaugeMetricFamily
            setattr(self, '_Collector__nexsan_perf_{}'.format(x), c('nexsan_perf_{}'.format(x), '', labels=['controller', 'port']))
        self.__nexsan_perf_link_errors_total = CounterMetricFamily('nexsan_perf_link_errors_total', '', labels=['controller', 'port', 'name'])
        self.__nexsan_perf_load_ratio = GaugeMetricFamily('nexsan_perf_load_ratio', '', labels=['array', 'owner'])
        self.__nexsan_maid_good = GaugeMetricFamily('nexsan_maid_good', '')
        for x in ['active', 'idle', 'slow', 'stopped', 'off', 'standby', 'efficiency']:
            setattr(self, '_Collector__nexsan_maid_{}_ratio'.format(x), GaugeMetricFamily('nexsan_maid_{}_ratio'.format(x), '', labels=['group']))

    def isgood(self, elem):
        if elem.attrib['good'] == 'yes':
            return 1
        else:
            return 0

    def collect(self):
        for child in self.__opstats.iterfind('./*'):
            if child.tag == 'nexsan_sys_details':
                self.collect_sys_details(child)
            elif child.tag == 'nexsan_env_status':
                self.collect_env_status(child)
            elif child.tag == 'nexsan_volume_stats':
                self.collect_volume_stats(child)
            elif child.tag == 'nexsan_perf_status':
                self.collect_perf_status(child)
            elif child.tag == 'nexsan_maid_stats':
                self.collect_maid_stats(child)

        yield from (v for k, v in self.__dict__.items() if k.startswith('_Collector__nexsan_'))

    def collect_sys_details(self, sys_details):
        self.__nexsan_sys_details.add_metric([sys_details.findtext('./' + l) for l in self.__nexsan_sys_details._labelnames], 1)
        self.__nexsan_sys_date.add_metric([], int(sys_details.findtext('./date')))

    def collect_env_status(self, env_status):
        for psu in env_status.iterfind('.//psu'):
            self.collect_psu(psu)
        for c in env_status.iterfind('.//controller'):
            self.collect_controller(c)
        for pod in env_status.iterfind('.//pod'):
            self.collect_pod(pod)

    def collect_psu(self, psu):
        parent = self.__parent_map[psu]
        values = [psu.attrib['id'], parent.attrib['id'] if parent.tag == 'enclosure' else '']

        self.__nexsan_env_psu_power_good.add_metric(values, self.isgood(psu.find('./state')))
        state = psu.find('./state')
        if 'power_watt' in state.attrib:
            self.__nexsan_env_psu_power_watts.add_metric(values, int(state.attrib['power_watt']))

        try:
            x = int(psu.find('./temperature_deg_c').text)
        except ValueError:
            pass
        else:
            self.__nexsan_env_psu_temp_celsius.add_metric(values, x)

        self.__nexsan_env_psu_temp_good.add_metric(values, self.isgood(psu.find('./temperature_deg_c')))

        for b in psu.iterfind('./blower_rpm'):
            self.__nexsan_env_psu_blower_rpm.add_metric(values + [b.attrib['id']], int(b.text))
            self.__nexsan_env_psu_blower_good.add_metric(values + [b.attrib['id']], self.isgood(b))

    def collect_controller(self, controller):
        parent = self.__parent_map[controller]
        values = [controller.attrib['id'], parent.attrib['id'] if parent.tag == 'enclosure' else '']

        for v in controller.iterfind('./voltage'):
            self.__nexsan_env_controller_voltage_volts.add_metric(values + [v.attrib['id']], float(v.text))
            self.__nexsan_env_controller_voltage_good.add_metric(values + [v.attrib['id']], self.isgood(v))

        for t in controller.iterfind('./temperature_deg_c'):
            self.__nexsan_env_controller_temp_celsius.add_metric(values + [t.attrib.get('id', '')], float(t.text))
            self.__nexsan_env_controller_temp_good.add_metric(values + [t.attrib.get('id', '')], self.isgood(t))

        for b in controller.iterfind('./battery'):
            self.__nexsan_env_controller_battery_charge_good.add_metric(values + [b.attrib['id']], self.isgood(b.find('./charge_state')))

    def collect_pod(self, pod):
        values = [pod.attrib['id'], self.__parent_map[pod].attrib['id']]

        for v in pod.iterfind('./voltage'):
            self.__nexsan_env_pod_voltage_volts.add_metric(values + [v.attrib['id']], float(v.text))
            self.__nexsan_env_pod_voltage_good.add_metric(values + [v.attrib['id']], self.isgood(v))

        for t in pod.iterfind('./temperature_deg_c'):
            self.__nexsan_env_pod_temp_celsius.add_metric(values + [t.attrib['id']], float(t.text))
            self.__nexsan_env_pod_temp_good.add_metric(values + [t.attrib['id']], self.isgood(t))

        for b1 in pod.iterfind('./front_panel/blower_rpm'):
            self.__nexsan_env_pod_front_blower_rpm.add_metric(values + [b1.attrib['id']], float(b1.text))
            self.__nexsan_env_pod_front_blower_good.add_metric(values + [b1.attrib['id']], self.isgood(b1))

        for b2 in pod.iterfind('./fan_tray/blower_rpm'):
            self.__nexsan_env_pod_tray_blower_rpm.add_metric(values + [b2.attrib['id']], float(b2.text))
            self.__nexsan_env_pod_tray_blower_good.add_metric(values + [b2.attrib['id']], self.isgood(b2))

    def collect_volume_stats(self, volume_stats):
        for volume in volume_stats.iterfind('./volume'):
            self.collect_volume(volume)

    def collect_volume(self, volume):
        values = [volume.attrib['id'], volume.attrib['name'], volume.attrib['array'], volume.attrib['serial_number']]

        for path in volume.iterfind('./path'):
            path_values = values + [path.attrib['init_ident'], path.attrib['target_id'], path.attrib['lun']]

            self.__nexsan_volume_ios_total.add_metric(path_values, int(path.findtext('./total_ios')))
            self.__nexsan_volume_ios_read_total.add_metric(path_values, int(path.findtext('./read_ios')))
            self.__nexsan_volume_ios_write_total.add_metric(path_values, int(path.findtext('./write_ios')))
            self.__nexsan_volume_blocks_read_total.add_metric(path_values, int(path.findtext('./read_blocks')))
            self.__nexsan_volume_blocks_write_total.add_metric(path_values, int(path.findtext('./write_blocks')))

    def collect_perf_status(self, perf):
        for controller in perf.iterfind('./controller'):
            values = [controller.attrib['id']]

            self.__nexsan_perf_cpu_usage_percent.add_metric(values, int(controller.findtext('./cpu_percent')))
            self.__nexsan_perf_memory_usage_percent.add_metric(values, int(controller.findtext('./memory_percent')))

            for port in controller.iterfind('./port'):
                port_values = values + [port.attrib['name']]

                self.__nexsan_perf_read_bytes_per_second.add_metric(port_values, 1024 * 1024 * int(port.findtext('./read_mbytes_per_sec')))
                self.__nexsan_perf_write_bytes_per_second.add_metric(port_values, 1024 * 1024 * int(port.findtext('./write_mbytes_per_sec')))
                self.__nexsan_perf_read_ios_total.add_metric(port_values, int(port.findtext('./read_ios')))
                self.__nexsan_perf_write_ios_total.add_metric(port_values, int(port.findtext('./write_ios')))
                self.__nexsan_perf_read_blocks_total.add_metric(port_values, int(port.findtext('./read_blocks')))
                self.__nexsan_perf_write_blocks_total.add_metric(port_values, int(port.findtext('./write_blocks')))
                self.__nexsan_perf_port_resets_total.add_metric(port_values, int(port.findtext('./port_resets')))
                self.__nexsan_perf_lun_resets_total.add_metric(port_values, int(port.findtext('./lun_resets')))

                for le in port.iterfind('./link_errors/link_error'):
                    self.__nexsan_perf_link_errors_total.add_metric(port_values + [le.attrib['error_name']], int(le.attrib['count']))

        for array in perf.iterfind('./array'):
            self.__nexsan_perf_load_ratio.add_metric([array.attrib['name'], array.findtext('./owner')], int(array.findtext('./load_percent'))/100)

    def collect_maid_stats(self, maid):
        self.__nexsan_maid_good.add_metric([], self.isgood(maid.find('./maid_stats_status')))

        for group in maid.iterfind('./maid_group'):
            for x in ['active', 'idle', 'slow', 'stopped', 'off', 'standby', 'efficiency']:
                elem = group.findtext('./{}_percent'.format(x))
                if elem is not None:
                    getattr(self, '_Collector__nexsan_maid_{}_ratio'.format(x)).add_metric([group.attrib['name']], int(elem)/100)
